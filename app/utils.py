import logging
import os
import re
import subprocess
import time
import timeit
from os import path
from typing import Dict, List, Tuple

import requests
from flask import request
from trankit import Pipeline

from .config import settings
from .models.audio_segment import AudioSegment

logger = logging.getLogger(__name__)

p = Pipeline(lang="vietnamese", gpu=False, cache_dir=settings.CACHE_DIR)


def upload_file() -> str:
    file = request.files["file"]
    filename = f"uploaded_file_{timeit.default_timer()}.wav"
    dst_file = path.join(settings.UPLOAD_DIR, filename)
    file.save(dst_file)
    logger.info(f"Upload file done. File save at {dst_file}")
    return filename

    # elapsed = timeit.default_timer() - start_time
    # return filename


def preprocess(filename: str) -> List[AudioSegment]:
    infile_path = path.join(settings.UPLOAD_DIR, filename)
    format_file = path.join(settings.UPLOAD_DIR, f"format_{filename}")
    left_file = path.join(settings.UPLOAD_DIR, f"left_{filename}")
    right_file = path.join(settings.UPLOAD_DIR, f"right_{filename}")

    # convert uploaded audio file to wav file with noise reduction
    subprocess.call(
        [
            "ffmpeg",
            "-i",
            infile_path,
            "-acodec",
            "pcm_s16le",
            "-ar",
            "16000",
            "-af",
            "aresample=resampler=soxr:precision=28:cheby=1,highpass=f=200,lowpass=f=3000,afftdn=nt=w:om=o",
            format_file,
            "-y",
        ]
    )

    # Split the audio by channels
    logger.info("Doing spliting audio by channel")
    subprocess.call(
        [
            "ffmpeg",
            "-i",
            format_file,
            "-map_channel",
            "0.0.0",
            left_file,
            "-map_channel",
            "0.0.1",
            right_file,
        ]
    )

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


def process_audio_sentence(input_sen, channel, call_id, customer_text_sum="") -> str:
    # convert speech to text by using dinosoft api
    if path.exists(input_sen):
        text = speech_to_text(input_sen)
    else:
        text = input_sen

    if not text:
        return ""

    extract_info_line = {}
    extract_info_sum = {}
    if channel == 2:  # only extract info from customer channel

        # extract info from this sentence
        extract_info_line = extract_customer_info(text)
        # print("extract_info_line:")
        # pprint(extract_info_line)

        # extract info from up to now customer conversation
        extract_info_sum = extract_customer_info(customer_text_sum + " " + text)
        # print("extract_info_sum:")
        # pprint(extract_info_sum)

    # get result and push web socket to GUI display in dialog
    logger.info(
        f"send STT result: text='{text}' channel={channel} call_id={call_id} info={extract_info_line}"
    )
    send_msg(text, channel, call_id, extract_info_line, extract_info_sum)

    return text


def extract_customer_info(text):
    """ Doing entities regconition """
    # name entity recoginition
    name_list, address_list = parse_name_entity(text)

    # parse cmnd, sdt
    id_number, phone_number = parse_id_phone_number(text)

    extract_info = {}
    extract_info["nameList"] = ",".join(name_list)
    extract_info["addressList"] = ",".join(address_list)
    extract_info["idNumber"] = id_number
    extract_info["phoneNumber"] = phone_number

    return extract_info


def extract_identity_info(text: str) -> Dict:
    name_list, address_list = parse_name_entity(text)
    id_number, phone_number = parse_id_phone_number(text)
    return {
        "name": name_list,
        "address": address_list,
        "id_number": id_number,
        "phone_number": phone_number,
    }


def do_vad_split(infile: str, channel: int) -> List[AudioSegment]:

    output = subprocess.run(
        [
            "ffmpeg",
            "-i",
            infile,
            "-af",
            "silencedetect=noise=-22dB:d=1",
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
                audio_file=infile,
            )
        ]

    file_splits = os.path.splitext(infile)
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
            infile,
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
        logger.warning("STT Engine returns nothings")
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


def start_call() -> None:
    data = {
        "caller": "customer",
        "agentId": "agent",
        "isOutbound": True,
        "criticalScore": 1,
    }

    r = requests.post(settings.API_URL + "/public/stt/call/start", json=data)
    json_result = r.json()
    call_id = json_result["model"]["id"]
    logger.info(f"Successfully started the call with ID={call_id}")
    return call_id


def stop_call(call_id, audio_file):
    data = {
        "id": call_id,
        # "sentiment": str(sentiment[0][0]),
        # "topic": topic
        "endTime": round(time.time() * 1000),
        "audioPath": settings.SITE_URL + "/" + settings.UPLOAD_DIR + "/" + audio_file,
    }
    requests.post(settings.API_URL + "/public/stt/call/finish", json=data)
    logger.info(f"Sucessfully stopped the call {call_id}")


def send_msg(
    msg: str = None,
    channel: int = None,
    call_id: int = None,
    extract_info_line: Dict = None,
    extract_info_sum: Dict = None,
) -> None:
    data = {
        "callId": call_id,
        "line": "agent" if channel == 1 else "customer",
        "textContent": msg,
        # "audioPath": "/audio/test",
        "startTime": int(time.time() * 1000),
        "extractInfoLine": extract_info_line,
        "extractInfoSum": extract_info_sum,
    }

    requests.post(settings.API_URL + "/public/stt/call/conversation", json=data)


def parse_name_entity(text: str) -> Tuple[List[str], List[str]]:
    # text = text.upper()
    text = num_mapping(text)

    # name entity recognition
    vi_output = p.ner(text)
    name_list = []
    address_list = []

    # token_list = vi_output["sentences"][0]["tokens"]
    sentences = vi_output["sentences"]
    for sentence in sentences:
        for token in sentence["tokens"]:
            if token["ner"] == "B-PER":
                name_list.append(token["text"])
            if "LOC" in token["ner"]:
                address_list.append(token["text"])

    return name_list, address_list


def num_mapping(text):
    # add leading space to avoid replace the match inside of the words such as agribank
    numeric_mappings = {
        " không": " 0",
        " một": " 1",
        " hai": " 2",
        " ba": " 3",
        " bốn": " 4",
        " năm": " 5",
        " lăm": " 5",
        " sáu": " 6",
        " bảy": " 7",
        " tám": " 8",
        " chín": " 9",
    }

    for pattern, repl in numeric_mappings.items():
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)

    return text


# from vietnam_number import w2n_single, w2n_couple
def parse_id_phone_number(text) -> Tuple[str, str]:

    text = num_mapping(text)

    # Remove all the words affect the pattern matching
    BAD_WORDS = [r"\s", "ạ", "dạ", "rồi"]
    text = re.sub("|".join(BAD_WORDS), "", text)
    # for word in BAD_WORDS:
    #     text = re.sub(word, "", text)

    # print(f"start extracting from text: {text}")

    # Extract the identity information by pattern matching
    # adding a single non-numeric character to avoid the case that
    # longer pattern would cover the shorter pattern leads to wrong extraction

    # regex to match phone number in VN (as standard)
    PHONE_REGEX = r"(0?)(3[2-9]|5[6|8|9]|7[0|6-9]|8[0-6|8|9]|9[0-4|6-9])\d{7,8}[^\d]"

    # regex to match ID number (new format)
    ID_REGEX = r"0?([0-8]\d|9[0-6])\d{9}[^\d]"

    # regex to match ID number (old format)
    ID_REGEX_OLD = r"(0?[1-8]\d|09[0-25]|[1-2]\d{2}|3[0-8]\d)\d{6}[^\d]"

    id_number = extract_info(ID_REGEX, text)
    if id_number == "":
        id_number = extract_info(ID_REGEX_OLD, text)

    phone_number = extract_info(PHONE_REGEX, text)

    return id_number, phone_number


def extract_info(regex: str, text: str) -> str:
    match = re.search(regex, text)
    if match is None:
        return ""

    # remove last non-numeric character
    start, end = match.span()
    return text[start : end - 1]  # noqa: E203
