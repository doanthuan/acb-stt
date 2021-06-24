from utils import *

#send_msg("xin chào", 2)
msg = "xin chào"
channel = 2
call_id = 295
extract_info = {}
extract_info["nameList"] = "name_list"
extract_info["addressList"] = "address_list"
extract_info["idNumber"] = "id_number"
extract_info["phoneNumber"] = "phone_number"
send_msg(msg, channel, call_id, extract_info, extract_info)