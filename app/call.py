import logging
import time
from typing import Dict

import requests

from .config import settings

logger = logging.getLogger(__name__)


def start_call() -> None:
    data = {
        "caller": "customer",
        "agentId": "agent",
        "isOutbound": True,
        "criticalScore": 1,
    }

    r = requests.post(settings.API_URL + "/public/stt/call/start", json=data)
    logger.info(f"response: {r}")
    json_result = r.json()
    call_id = json_result["model"]["id"]
    logger.info(f"Successfully started the call with ID={call_id}")
    return call_id


def stop_call(call_id, audio_file, audio_duration):
    data = {
        "id": call_id,
        # "sentiment": str(sentiment[0][0]),
        # "topic": topic
        "endTime": round(time.time() * 1000),
        "audioPath": settings.SITE_URL + "/f/" + audio_file,
        "audioLength": audio_duration,
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

    # round the startTime cause the timestamp equal in customer channel and agent channel ???
    data = {
        "callId": call_id,
        "line": "agent" if channel == 1 else "customer",
        "textContent": msg,
        # "audioPath": "/audio/test",
        # "startTime": round(time.time() * 1000),
        "extractInfoLine": extract_info_line,
        "extractInfoSum": extract_info_sum,
    }

    requests.post(settings.API_URL + "/public/stt/call/conversation", json=data)
