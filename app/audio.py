import logging
import os
import subprocess
from typing import List

from .config import settings
from .models.audio_segment import AudioSegment

logger = logging.getLogger(__name__)


def convert_to_wav(infile: str, outfile: str):
    subprocess.check_call(
        ["ffmpeg", "-i", infile, "-acodec", "pcm_s16le", outfile, "-y"]
    )


def split_by_channels(infile: str, left_outfile: str, right_outfile: str):
    subprocess.check_call(
        [
            "ffmpeg",
            "-i",
            infile,
            "-filter_complex",
            "[0:a]channelsplit=channel_layout=stereo[left][right]",
            "-map",
            "[left]",
            left_outfile,
            "-map",
            "[right]",
            right_outfile,
        ]
    )


def resample_audio_file(infile: str, outfile: str):
    subprocess.call(
        [
            "ffmpeg",
            "-i",
            infile,
            "-ar",
            "16000",
            "-af",
            "highpass=f=200,lowpass=f=3000",
            # "highpass=f=200,lowpass=f=3000,afftdn=nt=w:om=o",
            # "aresample=resampler=soxr:precision=28:cheby=1,highpass=f=200,lowpass=f=3000,afftdn=nt=w:om=o",
            outfile,
            "-y",
        ]
    )


def do_vad_split(infile: str, channel: int) -> List[AudioSegment]:
    resampled_file = "resampled_" + os.path.basename(infile)
    resampled_file = os.path.join(settings.UPLOAD_DIR, resampled_file)

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
        commands.extend(["-i", infile, audio_file])
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
    # audio_files = glob.glob(f"{file_splits[0]}_*")
    # audio_files.sort()
    # return audio_files


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
