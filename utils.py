import glob
import os
import re
import subprocess
import timeit
from datetime import datetime
from os import path
from typing import Dict, Iterator, List, Tuple

import requests
from flask import request
from marshmallow.utils import pprint
from trankit import Pipeline

from .config import settings

p = Pipeline(lang="vietnamese", gpu=False, cache_dir=settings.CACHE_DIR)


def upload_file() -> str:
    file = request.files["file"]
    filename = f"uploaded_file_{timeit.default_timer()}.wav"
    file.save(path.join(settings.UPLOAD_DIR, filename))
    return filename

    # elapsed = timeit.default_timer() - start_time
    # return filename


def preprocess(filename: str) -> Iterator[Tuple[str, str]]:
    # os.system('ffmpeg -i %s -ar 16000 -ac 1 -ab 256000 upload/upload.wav -y' % filename)
    infile_path = path.join(settings.UPLOAD_DIR, filename)
    format_file = path.join(settings.UPLOAD_DIR, f"format_{filename}")
    left_file = path.join(settings.UPLOAD_DIR, f"left_{filename}")
    right_file = path.join(settings.UPLOAD_DIR, f"right_{filename}")
    # subprocess.call(['ffmpeg', '-i', "upload/"+filename, '-ar', '16000', '-ac', '1', '-ab', '256000', "upload/"+ format_file, '-y'])
    # subprocess.call(['ffmpeg', '-i', "upload/"+filename, '-ar', '16000', '-af','afftdn=nf=-20', "upload/"+ format_file, '-y'])
    subprocess.call(
        [
            "ffmpeg",
            "-i",
            infile_path,
            "-ar",
            "16000",
            "-af",
            "highpass=f=200, lowpass=f=3000",
            format_file,
            "-y",
        ]
    )

    # split audio by channels
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

    # split sentences by silence
    # subprocess.call(['ffmpeg', '-i', "upload/"+left_file, '-af', 'silencedetect=noise=-20dB:d=1', '-f', 'null', '-', '2>', 'vol.txt'])
    left_sentences = do_vad_split(left_file)
    right_sentences = do_vad_split(right_file)
    list_sentences = zip(left_sentences, right_sentences)

    return list_sentences


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
        print("extract_info_line:")
        pprint(extract_info_line)

        # extract info from up to now customer conversation
        extract_info_sum = extract_customer_info(customer_text_sum + " " + text)
        print("extract_info_sum:")
        pprint(extract_info_sum)

    # get result and push web socket to GUI display in dialog
    send_msg(text, channel, call_id, extract_info_line, extract_info_sum)

    return text


def extract_customer_info(text):
    # name entity recoginition
    name_list, address_list = parse_name_entity(text)

    # parse cmnd, sdt
    id_number, phone_number = parse_id_phone_number(text)

    extract_info = {}
    extract_info["nameList"] = name_list
    extract_info["addressList"] = address_list
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


def do_vad_split(infile: str) -> List[str]:

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
    print(f"SILENCES: {silences}")

    # No silience found, no need to split the audio
    if len(silences) == 0:
        return [infile]

    file_splits = os.path.splitext(infile)
    current_split = 0

    # for the case first silence_start != 0
    if silences[0] != 0:
        commands = [
            "ffmpeg",
            "-t",
            str(silences[0] + 2 * 0.25),
            "-i",
            infile,
            f"{file_splits[0]}_{current_split:03}{file_splits[1]}",
        ]
        subprocess.run(
            commands,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        current_split += 1

    for idx in range(1, len(silences), 2):
        commands = [
            "ffmpeg",
            "-ss",
            str(silences[idx] - 0.25),
        ]
        if idx + 1 < len(silences):
            commands.extend(["-t", str(silences[idx + 1] - silences[idx] + 2 * 0.25)])
        commands.extend(
            [
                "-i",
                infile,
                f"{file_splits[0]}_{current_split:03}{file_splits[1]}",
            ]
        )
        subprocess.run(
            commands,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        current_split += 1
    audio_files = glob.glob(f"{file_splits[0]}_*")
    audio_files.sort()
    return audio_files


def speech_to_text(filename: str) -> str:

    result = ""
    audio_file = path.join(path.dirname(path.realpath(__file__)), filename)

    # data = {"apiKey": settings.STT_API_KEY}
    files = {"file": open(audio_file, "rb")}
    r = requests.post(settings.API_STT, files=files)  # , data=data)
    # print(data)

    if not r.ok:
        print("Something went wrong!")
        print(r)
        return ""

    print("Upload completed successfully!")
    response = r.json()
    result = parse_stt_result(response)
    # print(result)

    return result


def parse_stt_result(json_result: Dict) -> str:
    if not json_result["results"]:
        print("STT Engine returns nothings")
        return ""
    
    result = json_result["results"]
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
        "agentId": 1102,
        "isOutbound": True,
        "startTime": str(datetime.now()),
        "endTime": "",
        "criticalScore": 1,
    }

    r = requests.post(settings.API_URL + "/public/stt/call/start", json=data)
    json_result = r.json()
    return json_result


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
        "audioPath": "/audio/test",
        "startTime": str(datetime.date(datetime.now())),
        "extractInfoLine": extract_info_line,
        "extractInfoSum": extract_info_sum,
    }

    requests.post(settings.API_URL + "/public/stt/call/conversation", json=data)


def parse_name_entity(text: str) -> Tuple[List[str], List[str]]:
    text = text.upper()
    text = num_mapping(text)
    print(text)

    # name entity recognition
    vi_output = p.ner(text)

    token_list = vi_output["sentences"][0]["tokens"]

    name_list = []
    address_list = []
    for token in token_list:
        if token["ner"] == "B-PER":
            name_list.append(token["text"])
        if "LOC" in token["ner"]:
            address_list.append(token["text"])

    return name_list, address_list


def num_mapping(text):
    numeric_mappings = {
        "không": "0",
        "một": "1",
        "hai": "2",
        "ba": "3",
        "bốn": "4",
        "năm": "5",
        "sáu": "6",
        "bảy": "7",
        "tám": "8",
        "chín": "9",
    }

    for pattern, repl in numeric_mappings.items():
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)

    return text


# from vietnam_number import w2n_single, w2n_couple
def parse_id_phone_number(text) -> Tuple[str, str]:

    text = num_mapping(text)

    # trim all the space character
    text = re.sub(r"\s", "", text)

    # regex to match phone number in VN (as standard)
    PHONE_REGEX = r"(0?)(3[2-9]|5[6|8|9]|7[0|6-9]|8[0-6|8|9]|9[0-4|6-9])\d{7,8}"

    # regex to match ID number (new format)
    ID_REGEX = r"0([0-8]\d|9[0-6])\d{9}"

    # regex to match ID number (old format)
    ID_REGEX_OLD = r"(0[1-8]\d|09[0-25]|[1-2]\d{2}|3[0-8]\d)\d{6}"

    id_number = extract_info(ID_REGEX, text)
    if id_number == "":
        id_number = extract_info(ID_REGEX_OLD, text)

    phone_number = extract_info(PHONE_REGEX, text)

    return id_number, phone_number


def extract_info(regex: str, text: str) -> str:
    match = re.search(regex, text)
    if match is None:
        return ""

    start, end = match.span()
    return text[start + 1 : end]  # noqa: E203
