import contextlib
import logging
import os
import re
import subprocess
import wave
from datetime import datetime, timedelta
from typing import List

import webrtcvad

from .config import settings
from .models.audio_segment import AudioSegment
from .silero.utils import (get_speech_ts_adaptive, init_jit_model, read_audio,
                           save_audio)
from .vad import frame_generator, vad_collector

logger = logging.getLogger(__name__)


def convert_to_wav(infile: str, outfile: str):
    subprocess.check_call(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            infile,
            "-acodec",
            "pcm_s16le",
            outfile,
            "-y",
        ]
    )


def split_by_channels(infile: str, left_outfile: str, right_outfile: str):
    # subprocess.check_call(
    #     [
    #         "ffmpeg",
    #         "-hide_banner",
    #         "-loglevel",
    #         "error",
    #         "-i",
    #         infile,
    #         "-filter_complex",
    #         "[0:a]channelsplit=channel_layout=stereo[left][right]",
    #         "-map",
    #         "[left]",
    #         left_outfile,
    #         "-map",
    #         "[right]",
    #         right_outfile,
    #     ]
    # )
    subprocess.check_call(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            infile,
            "-map_channel",
            "0.0.0",
            left_outfile,
            "-map_channel",
            "0.0.1",
            right_outfile,
            "-y",
        ]
    )


def resample_audio_file(infile: str, outfile: str):
    subprocess.call(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            infile,
            "-ar",
            "16000",
            "-ac",
            "1",
            "-af",
            # "highpass=f=200,lowpass=f=3000",
            # "highpass=f=200,lowpass=f=3000,afftdn=nt=w:om=o",
            "aresample=resampler=soxr:precision=30:cheby=1,highpass=f=200,lowpass=f=3000,afftdn=nt=w:om=o",
            outfile,
            "-y",
        ]
    )


def denoise_audio(infile: str, outfile: str):
    subprocess.check_call(
        [
            "sox",
            infile,
            outfile,
            "noisered",
            settings.NOISE_PROFILE,
            str(settings.NOISE_SENSITIVITY),
        ]
    )


def do_silero_vad_split(infile: str, channel: int) -> List[AudioSegment]:
    resampled_file = "resampled_" + os.path.basename(infile)
    resampled_file = os.path.join(settings.UPLOAD_DIR, resampled_file)

    # resample audio file at 16khz, with/without noise reduction
    resample_audio_file(infile, resampled_file)
    in_wav = read_audio(resampled_file)

    silero_model = init_jit_model(settings.SILERO_MODEL)
    speech_timestamps = get_speech_ts_adaptive(in_wav, silero_model)

    res = []
    filename = os.path.splitext(resampled_file)[0]
    for i, ts in enumerate(speech_timestamps):
        path = f"{filename}_chunk_{i:003}.wav"
        save_audio(path, in_wav[ts["start"] : ts["end"]], 16000)
        res.append(
            AudioSegment(timestamp=ts["start"], channel=channel, audio_file=path)
        )
    return res


def do_webrtcvad_split(infile: str, channel: int) -> List[AudioSegment]:
    resampled_file = "resampled_" + os.path.basename(infile)
    resampled_file = os.path.join(settings.UPLOAD_DIR, resampled_file)

    # resample audio file at 16khz, with/without noise reduction
    resample_audio_file(infile, resampled_file)
    audio_path, sample_rate = read_wave(resampled_file)
    logger.info(
        f"collect voice audio using VAD.  aggressive={settings.VAD_AGGRESSIVE_LEVEL} frame_duration={settings.FRAME_DURATION_MS} padding={settings.PADDING_DURATION_MS}"
    )

    vad = webrtcvad.Vad(settings.VAD_AGGRESSIVE_LEVEL)
    frames = frame_generator(settings.FRAME_DURATION_MS, audio_path, sample_rate)
    frames = list(frames)

    filename = os.path.splitext(resampled_file)[0]
    segments = vad_collector(
        sample_rate,
        settings.FRAME_DURATION_MS,
        settings.PADDING_DURATION_MS,
        vad,
        frames,
    )

    res = []
    for i, segment in enumerate(segments):
        path = f"{filename}_chunk_{i:003}.wav"
        write_wave(path, segment.bytes, sample_rate)
        res.append(
            AudioSegment(timestamp=segment.timestamp, channel=channel, audio_file=path)
        )
    return res


def do_vad_split(infile: str, channel: int) -> List[AudioSegment]:
    resampled_file = "resampled_" + os.path.basename(infile)
    resampled_file = os.path.join(settings.UPLOAD_DIR, resampled_file)

    # resample audio file at 16khz, with/without noise reduction
    resample_audio_file(infile, resampled_file)

    logger.info(
        f"split into smaller audio file by silence. noise={settings.NOISE_LEVEL} duration={settings.NOISE_DURATION}"
    )
    output = subprocess.run(
        [
            "ffmpeg",
            "-i",
            resampled_file,
            "-af",
            f"silencedetect=noise={settings.NOISE_LEVEL}dB:d={settings.NOISE_DURATION}",
            "-f",
            "null",
            "-",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    silences = []
    for line in output.stdout.decode("utf-8").splitlines():
        if "silence_" in line:
            start_idx = line.find(":") + 1
            if "|" in line:
                time_offset = float(
                    line[start_idx : line.find("|")].strip()  # noqa: E203
                )
            else:
                time_offset = float(line[start_idx:].strip())
            silences.append(time_offset)
    logger.debug(f"Silences found: {silences}")

    # No silience found, no need to split the audio
    if len(silences) == 0:
        return [
            AudioSegment(
                timestamp=0,
                channel=channel,
                audio_file=resampled_file,
            )
        ]

    file_splits = os.path.splitext(resampled_file)
    current_split = 0

    # for the case first silence_start != 0
    res = []
    if silences[0] != 0:
        audio_file = f"{file_splits[0]}_{current_split:03}{file_splits[1]}"
        commands = [
            "ffmpeg",
            "-t",
            str(silences[0] + 2 * 0.25),
            "-i",
            resampled_file,
            audio_file,
        ]
        subprocess.run(
            commands,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        res.append(AudioSegment(timestamp=0, channel=channel, audio_file=audio_file))
        current_split += 1

    # split the audio file into smaller audio segments with silience trimmed
    for idx in range(1, len(silences), 2):
        commands = [
            "ffmpeg",
            "-ss",
            str(silences[idx] - 0.25),
        ]
        if idx + 1 < len(silences):
            commands.extend(["-t", str(silences[idx + 1] - silences[idx] + 2 * 0.25)])

        audio_file = f"{file_splits[0]}_{current_split:03}{file_splits[1]}"
        commands.extend(["-i", resampled_file, audio_file])
        subprocess.run(
            commands,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        current_split += 1
        res.append(
            AudioSegment(
                timestamp=silences[idx], channel=channel, audio_file=audio_file
            )
        )
    return res


def get_num_channels(infile: str) -> int:
    output = subprocess.run(
        ["ffprobe", infile], stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    filter_output = re.findall(r"\d channels", output.stdout.decode("utf-8"))
    if len(filter_output) > 0:
        return int(filter_output[0].split(" ")[0])


def get_audio_duration(infile: str) -> int:
    output = subprocess.run(
        ["ffprobe", infile], stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    filter_output = re.findall(r"Duration: \d+:\d+:\d+", output.stdout.decode("utf-8"))
    if len(filter_output) > 0:
        duration_str = filter_output[0].split("Duration: ")[1]
        t = datetime.strptime(duration_str, "%H:%M:%S")
        delta = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
        return int(delta.total_seconds())


def read_wave(path):
    """Reads a .wav file.
    Takes the path, and returns (PCM audio data, sample rate).
    """
    with contextlib.closing(wave.open(path, "rb")) as wf:
        num_channels = wf.getnchannels()
        assert num_channels == 1
        sample_width = wf.getsampwidth()
        assert sample_width == 2
        sample_rate = wf.getframerate()
        assert sample_rate in (8000, 16000, 32000, 48000)
        pcm_data = wf.readframes(wf.getnframes())
        return pcm_data, sample_rate


def write_wave(path, audio, sample_rate):
    """Writes a .wav file.
    Takes path, PCM audio data, and sample rate.
    """
    with contextlib.closing(wave.open(path, "wb")) as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio)


def process_audio_sentence(input_sen, channel, call_id, customer_text_sum="") -> str:
    pass
    # # convert speech to text by using dinosoft api
    # if os.path.exists(input_sen):
    #     text = speech_to_text(input_sen)
    # else:
    #     text = input_sen

    # if not text:
    #     return ""

    # extract_info_line = {}
    # extract_info_sum = {}
    # if channel == 2:  # only extract info from customer channel

    #     # extract info from this sentence
    #     extract_info_line = extract_customer_info(text)
    #     # print("extract_info_line:")
    #     # pprint(extract_info_line)

    #     # extract info from up to now customer conversation
    #     extract_info_sum = extract_customer_info(customer_text_sum + " " + text)
    #     # print("extract_info_sum:")
    #     # pprint(extract_info_sum)

    # # get result and push web socket to GUI display in dialog
    # logger.info(
    #     f"send STT result: text='{text}' channel={channel} call_id={call_id} info={extract_info_line}"
    # )
    # send_msg(text, channel, call_id, extract_info_line, extract_info_sum)

    # return text
