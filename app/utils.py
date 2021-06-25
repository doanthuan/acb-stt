import logging
import timeit
from os import path
from typing import Dict, List

import requests
from flask import request

from .audio import convert_to_wav, do_vad_split, split_by_channels
from .call import send_msg
from .config import settings
from .models.audio_segment import AudioSegment
from .nlp import extract_customer_info

logger = logging.getLogger(__name__)


def upload_file() -> str:
    file = request.files["file"]
    filename = f"uploaded_file_{timeit.default_timer()}.wav"
    dst_file = path.join(settings.UPLOAD_DIR, filename)
    file.save(dst_file)
    logger.info(f"Upload file done. File save at {dst_file}")
    return filename


def preprocess(filename: str) -> List[AudioSegment]:
    # TODO: detect number of channels in the audio file for the voicemail
    infile_path = path.join(settings.UPLOAD_DIR, filename)
    format_file = path.join(settings.UPLOAD_DIR, f"format_{filename}")
    left_file = path.join(settings.UPLOAD_DIR, f"left_{filename}")
    right_file = path.join(settings.UPLOAD_DIR, f"right_{filename}")

    convert_to_wav(infile_path, format_file)
    split_by_channels(format_file, left_file, right_file)

    audio_segments = []
    audio_segments.extend(do_vad_split(left_file, 1))
    audio_segments.extend(do_vad_split(right_file, 2))
    audio_segments = sorted(audio_segments, key=lambda x: x.timestamp, reverse=False)

    return audio_segments


def do_stt_and_extract_info(
    call_id, audio_segment: AudioSegment, current_text: str = ""
) -> str:
    if not path.exists(audio_segment.audio_file):
        raise ValueError(f"Path {audio_segment.audio_file} does not exist")

    output_text = speech_to_text(audio_segment.audio_file)

    # As the STT output text is empty, no need to process further,
    # Just return the last current text for the next run
    if not output_text:
        return current_text

    current_text = " ".join([current_text, output_text])

    # attempt to extract customer info from current sentence and the entire
    # sentence
    customer_info = extract_customer_info(output_text)
    current_customer_info = extract_customer_info(current_text)

    logger.info(
        f"Send updated result: text='{output_text}' channel={audio_segment.channel} call_id={call_id} info={customer_info}"
    )
    send_msg(
        output_text,
        audio_segment.channel,
        call_id,
        customer_info,
        current_customer_info,
    )
    return current_text


def speech_to_text(filename: str) -> str:

    result = ""
    # audio_file = path.join(path.realpath(__file__).parent.absolute(), filename)
    audio_file = path.abspath(filename)

    # data = {"apiKey": settings.STT_API_KEY}
    files = {"file": open(audio_file, "rb")}
    r = requests.post(settings.API_STT, files=files)  # , data=data)
    # print(data)

    if not r.ok:
        logger.error("Something went wrong!")
        logger.error(r)
        return ""

    # print("Upload completed successfully!")
    response = r.json()
    # print(response)
    result = parse_stt_result(response)
    # print(result)

    return result


def parse_stt_result(json_result: Dict) -> str:
    if not json_result["result"]:
        logger.warning("Oops!!! STT Engine returns nothing")
        return ""

    result = json_result["result"]
    # result = []
    # for segment in json_result["Model"]:
    #     # multiple transcripts in hypotheses ???
    #     result.append(segment["result"]["hypotheses"][0]["transcript"])

    return " ".join(result)


def join_files(file1: str, file2: str) -> None:
    with open(file1, "ab") as outfile, open(file2, "rb") as infile:
        outfile.write(infile.read())
