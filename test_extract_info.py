from utils import (
    extract_identity_info,
    preprocess,
    process_audio_sentence,
    start_call,
    upload_file,
)

# start a call
call_id = start_call()

# right_sentences_text = [
#     "xin chào, tên tôi là Đoàn Vũ Thuận",
#     "chứng minh nhân dân số không hai bốn không một năm bốn ba sáu",
#     "địa chỉ nhà tôi năm chín hai xẹt một nguyễn văn quá quận mười hai",
#     "số điện thoại của tôi không chín không hai bảy hai bảy hai ba một",
#     ]

right_sentences_text = [
    "xin chào, tên tôi là Đoàn Vũ Thuận",
    "chứng minh nhân dân số không hai bốn ",
    "không một năm bốn ba sáu địa chỉ nhà tôi năm chín hai xẹt một nguyễn văn quá quận mười hai",
    "số điện thoại của tôi không chín không hai bảy hai bảy hai ba một",
    ]

customer_text_sum = ""
for right_sen in right_sentences_text:
    customer_text_sum += " " + process_audio_sentence(
        right_sen, 2, call_id, customer_text_sum
    )