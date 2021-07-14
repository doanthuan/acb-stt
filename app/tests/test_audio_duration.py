import contextlib
import logging
import os
import re
import subprocess
import wave
from typing import List
from datetime import datetime, timedelta

infile = "/home/thuan/acb-stt/demo/upload/01.mp3"
output = subprocess.run(
    ["ffprobe", infile], stdout=subprocess.PIPE, stderr=subprocess.STDOUT
)
filter_output = re.findall(r"Duration: \d+:\d+:\d+", output.stdout.decode("utf-8"))
#print(filter_output)
if len(filter_output) > 0:
    duration_str = (filter_output[0].split("Duration: ")[1])
    print(duration_str)
    t = datetime.strptime(duration_str, '%H:%M:%S')
    delta = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
    print(delta.total_seconds())