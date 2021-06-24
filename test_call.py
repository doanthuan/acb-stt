from app import stop_call
from utils import *

call_id = start_call()
print(call_id)
#send_msg("xin chào", 2)

# from datetime import datetime

# now = datetime.now()

# print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

stop_call(call_id,"test.mp3")