import logging
import time
from typing import Dict

import requests


call_id = 762

data = {
        "id": call_id,
        # "sentiment": str(sentiment[0][0]),
        # "topic": topic
        "endTime": round(time.time() * 1000),
        "audioPath": "test",
        "audioLength": 123,
    }
requests.post("http://172.23.224.1:60000/api/public/stt/call/finish", json=data)