# from trankit import Pipeline
# from nlp import *

import os

# import mysql.connector
import MySQLdb
from utils import extract_call_info


def test_a_call(call):

    print(f"AUDIO: {call['audio']}")
    cursor.execute(
        f"SELECT text_content FROM stt_call_conversation WHERE call_id={call['call_id']} AND line='customer' "
    )
    texts = cursor.fetchall()
    # for text in texts:
    #     print(text)

    criteria = {
        "detect_name": False,
        "detect_address": False,
        "detect_id": False,
        "detect_phone": False,
        # more fields
        "detect_card_no": False,
        "detect_acc_no": False,
    }

    current_text = {
        "names": "",
        "addresses": "",
        "id": "",
        "phone": "",
        "card_no": "",
        "acc_no": "",
    }
    for text in texts:
        customer_info, current_customer_info = extract_call_info(
            text[0], current_text, criteria, False
        )
        if customer_info["addressList"] != "":
            print(customer_info["addressList"])
        if current_customer_info["addressList"] != "":
            print(current_customer_info["addressList"])


db = MySQLdb.connect(
    host="localhost", user="root", password="root", database="gru-stt-acb"
)
cursor = db.cursor()

# get calls
cursor.execute("SELECT id, audio_path FROM stt_call WHERE id = 806")
rows = cursor.fetchall()
calls = []
for row in rows:
    calls.append({"call_id": row[0], "audio": os.path.basename(str(row[1]))})


# get call conversations
for call in calls:
    test_a_call(call)
