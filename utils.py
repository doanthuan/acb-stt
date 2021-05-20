import glob
import os
import subprocess
import timeit
from datetime import datetime
from os import path
from typing import Dict

import requests
from flask import request

from config import settings


def upload_file():
    file = request.files["file"]
    filename = f"uploaded_file_{timeit.default_timer()}.wav"
    file.save(path.join(settings.UPLOAD_DIR, filename))
    return filename

    # elapsed = timeit.default_timer() - start_time
    # return filename


def preprocess(filename):
    # os.system('ffmpeg -i %s -ar 16000 -ac 1 -ab 256000 upload/upload.wav -y' % filename)
    infile_path = path.join(settings.UPLOAD_DIR, filename)
    format_file = path.join(settings.UPLOAD_DIR, f"format_{filename}")
    left_file = path.join(settings.UPLOAD_DIR, f"left_{format_file}")
    right_file = path.join(settings.UPLOAD_DIR, f"right_{format_file}")
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


def process_audio_sentence(input_sen, channel, call_id):
    # convert speech to text by using dinosoft api
    text = speech_to_text(input_sen)

    # TODO: keyword detection + post actions if keyword matched

    # TODO: name entity recoginition

    # TODO: get result and push web socket to GUI display in dialog
    send_msg(text, channel, call_id)


def do_vad_split(infile):

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
                time_offset = float(line[start_idx : line.find("|")].strip())
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


def speech_to_text(filename):

    result = ""
    audio_file = path.join(path.dirname(path.realpath(__file__)), filename)

    data = {"apiKey": "api-642ce45e-d48c-4811-8cae-3de45027968a"}
    files = {"file": open(audio_file, "rb")}
    r = requests.post(settings.API_STT, files=files, data=data)

    if r.ok:
        print("Upload completed successfully!")
        response = r.json()
        result = parse_stt_result(response)
        print(result)
    else:
        print("Something went wrong!")

    return result


def parse_stt_result(json_result: Dict):
    if len(json_result["Model"]) == 0:
        print("STT Engine returns nothings")
        return ""

    result = []
    for segment in json_result["Model"]:
        # multiple transcripts in hypotheses ???
        result.append(segment["result"]["hypotheses"][0]["transcript"])

    return " ".join(result)


def join_files(file1, file2):
    with open(file1, "ab") as myfile, open(file2, "rb") as file2:
        myfile.write(file2.read())


def start_call():

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
    return json_result["model"]["id"]


def send_msg(msg, channel, call_id):
    line = "agent" if channel == 1 else "customer"
    data = {
        "callId": call_id,
        "line": line,
        "textContent": msg,
        "audioPath": "/audio/test",
        "startTime": str(datetime.now()),
    }

    try:
        requests.post(settings.API_URL + "/public/stt/call/conversation", json=data)
    except Exception as e:
        print("Unexpected exception occurred: ", e)
