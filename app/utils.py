import logging
from os import path
from typing import Dict, List

import paramiko
import requests
from flask import request

from .audio import (convert_to_wav, do_webrtcvad_split, get_audio_duration,
                    get_num_channels, split_by_channels)
from .call import send_msg
from .config import settings
from .models.audio_segment import AudioSegment
from .nlp import extract_customer_info

logger = logging.getLogger(__name__)


def upload_file() -> str:
    file = request.files["file"]
    logger.info(f'Upload_file: {request.files["file"]}')
    logger.info(f"Upload_file: {file.filename}")
    filename = file.filename
    dst_file = path.join(settings.UPLOAD_DIR, filename)
    file.save(dst_file)
    logger.info(f"Upload file done. File save at {dst_file}")
    return filename


def preprocess(filename: str) -> List[AudioSegment]:
    name = path.splitext(filename)

    # TODO: detect number of channels in the audio file for the voicemail
    infile_path = path.join(settings.UPLOAD_DIR, filename)
    format_file = path.join(settings.UPLOAD_DIR, f"format_{name[0]}.wav")
    left_file = path.join(settings.UPLOAD_DIR, f"left_{name[0]}.wav")
    right_file = path.join(settings.UPLOAD_DIR, f"right_{name[0]}.wav")

    convert_to_wav(infile_path, format_file)

    # split the file to smaller audio segments. If there is only 1 channel
    # => that is for customer
    audio_segments = []
    num_channels = get_num_channels(format_file)
    logger.info(f"Number of channels detected: {num_channels}")
    if num_channels > 1:
        logger.info("split audio to 2 channels")
        split_by_channels(format_file, left_file, right_file)
        # denoise_audio(left_file, left_file)
        audio_segments.extend(do_webrtcvad_split(left_file, 1))
        audio_segments.extend(do_webrtcvad_split(right_file, 2))
    else:
        logger.info("skip splitting by channels as there is only 1 channel")
        audio_segments.extend(do_webrtcvad_split(format_file, 2))
    audio_segments = sorted(audio_segments, key=lambda x: x.timestamp, reverse=False)
    audio_duration = get_audio_duration(format_file)

    return audio_segments, num_channels, audio_duration


def contains_keyword(keywords: List[str], text: str) -> bool:
    for keyword in keywords:
        if keyword in text:
            return True
    return False


def do_stt_and_extract_info(
    call_id: int = None,
    audio_segment: AudioSegment = None,
    current_text: Dict[str, str] = None,
    criteria: Dict = None,
    is_voice_message: bool = False,
) -> str:
    # TODO: refactoring
    if not path.exists(audio_segment.audio_file):
        raise ValueError(f"Path {audio_segment.audio_file} does not exist")

    output_text = speech_to_text(audio_segment.audio_file)

    customer_info, current_customer_info = extract_call_info(
        output_text, current_text, criteria, is_voice_message
    )

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
    return current_text, criteria


def extract_call_info(
    output_text: str,
    current_text: Dict[str, str] = None,
    criteria: Dict = None,
    is_voice_message: bool = False,
):
    # As the STT output text is empty, no need to process further,
    # Just return the last current text for the next run
    if not output_text:
        return current_text, criteria

    start_checking = False
    if is_voice_message:
        start_checking = True
        criteria["detect_phone"] = True
        criteria["detect_id"] = True
        criteria["detect_card_no"] = True
        criteria["detect_acc_no"] = True

    # always try detecting name, phone if voice message
    criteria["detect_name"] = True
    criteria["detect_address"] = True
    # else:
    #     # should be strict when agent ask
    #     start_checking = audio_segment.channel == 1

    if start_checking or contains_keyword(
        ["tên họ", "họ tên", "tên gì", "xưng hô"], output_text
    ):
        logger.info("`NAME` scanning is activated")
        criteria["detect_name"] = True

    # HACK: sometimes, customer introduces the name before-hand
    # if audio_segment.channel == 2 and contains_keyword(["mình là"], output_text):
    #     logger.info("Customer introduces himself/herself")
    #     criteria["detect_name"] = True

    if start_checking or contains_keyword(["địa chỉ", "số nhà"], output_text):
        logger.info("`ADDRESS` scanning is activated")
        criteria["detect_address"] = True

    if start_checking or contains_keyword(["chứng minh", "căn cước"], output_text):
        logger.info("`ID` scanning is activated")
        criteria["detect_id"] = True

    if start_checking or contains_keyword(["số điện thoại", "số di động"], output_text):
        logger.info("`PHONE_NUMBER` scanning is activated")
        criteria["detect_phone"] = True

    if start_checking or contains_keyword(["số thẻ"], output_text):
        logger.info("`CARD_NO` scanning is activated")
        criteria["detect_card_no"] = True

    if start_checking or contains_keyword(["số tài khoản"], output_text):
        logger.info("`ACC_NO` scanning is activated")
        criteria["detect_acc_no"] = True

    # Only save the entire text when the signal for detect `ID`, `PHONE`is on.
    # Otherwise, keep it as blank
    if criteria["detect_id"]:
        current_text["id"] = " ".join([current_text["id"], output_text])

    if criteria["detect_phone"]:
        current_text["phone"] = " ".join([current_text["phone"], output_text])

    if criteria["detect_acc_no"]:
        current_text["acc_no"] = " ".join([current_text["acc_no"], output_text])

    if criteria["detect_card_no"]:
        current_text["card_no"] = " ".join([current_text["card_no"], output_text])

    if criteria["detect_address"]:
        # print("address",current_text["addresses"])
        current_text["addresses"] = " ".join([current_text["addresses"], output_text])

    # attempt to extract customer info from current sentence and the entire sentence
    customer_info = extract_customer_info(output_text, criteria=criteria)
    current_customer_info = extract_customer_info(current_text, criteria=criteria)

    if customer_info["nameList"] != "" or current_customer_info["nameList"] != "":
        if criteria.get("detect_name") is True:
            logger.info("Found NAMES. Reset flag `detect_name`")
            logger.info("customer_info: {}".format(customer_info["nameList"]))
            logger.info(
                "current_customer_info: {}".format(current_customer_info["nameList"])
            )
        current_text["names"] = ""
        # criteria["detect_name"] = False

    if customer_info["addressList"] != "" or current_customer_info["addressList"] != "":
        if criteria.get("detect_address") is True:
            logger.info("Found address. Reset flag `detect_address`")
            logger.info("customer_info: {}".format(customer_info["addressList"]))
            logger.info(
                "current_customer_info: {}".format(current_customer_info["addressList"])
            )
        current_text["addresses"] = ""
        # Keep `detect_address` ON will handle the cases that addresses in multiple sentences
        # criteria["detect_address"] = False

    if customer_info["idNumber"] != "" or current_customer_info["idNumber"] != "":
        if criteria.get("detect_id") is True:
            logger.info("Found ID NUMBER. Reset flag `detect_id`")
            current_text["id"] = ""
        criteria["detect_id"] = False

    if customer_info["phoneNumber"] != "" or current_customer_info["phoneNumber"] != "":
        if criteria.get("detect_phone") is True:
            logger.info("Found PHONE NUMBER. Reset flag `detect_phone`")
            current_text["phone"] = ""
        criteria["detect_phone"] = False

    if customer_info["cardNumber"] != "" or current_customer_info["cardNumber"] != "":
        if criteria.get("detect_card_no") is True:
            logger.info("Found `CARD_NO`. Reset flag `detect_card_no`")
            current_text["card_no"] = ""
        criteria["detect_card_no"] = False

    if customer_info["accNumber"] != "" or current_customer_info["accNumber"] != "":
        if criteria.get("detect_acc_no") is True:
            logger.info("Found `ACC_NO`. Reset flag `detect_acc_no`")
            current_text["acc_no"] = ""
        criteria["detect_acc_no"] = False

    return customer_info, current_customer_info


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


def load_sftp_files():
    conn = None
    myftp = None

    try:
        conn = paramiko.SSHClient()
        conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        conn.connect(
            settings.SFTP_HOST,
            username=settings.SFTP_USER,
            password=settings.SFTP_PASSWORD,
        )
        myftp = conn.open_sftp()
        files = []
        for filename in myftp.listdir(settings.SFTP_DIR):
            if filename.endswith((".mp3", ".wav")):
                files.append(filename)
        return files
    finally:
        if myftp is not None:
            myftp.close()
        if conn is not None:
            conn.close()


def get_sftp_file(filename):
    conn = None
    myftp = None
    try:
        conn = paramiko.SSHClient()
        conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        conn.connect(
            settings.SFTP_HOST,
            username=settings.SFTP_USER,
            password=settings.SFTP_PASSWORD,
        )
        myftp = conn.open_sftp()
        myftp.get(
            f"{settings.SFTP_DIR}/{filename}", f"{settings.UPLOAD_DIR}/{filename}"
        )
    finally:
        if myftp is not None:
            myftp.close()
        if conn is not None:
            conn.close()
