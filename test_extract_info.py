from utils import *

# start a call
# call_id = start_call()

# right_sentences_text = [
#     "xin chào, tên tôi là Đoàn Vũ Thuận",
#     "chứng minh nhân dân số không hai bốn không một năm bốn ba sáu",
#     "địa chỉ nhà tôi năm chín hai xẹt một nguyễn văn quá quận mười hai",
#     "số điện thoại của tôi không chín không hai bảy hai bảy hai ba một",
#     ]

# right_sentences_text = [
#     "chị cho em hỏi chút được không ạ",
#     "em hôm qua chuyển tiền cho số tài khoản của phan thị là em nghi có hiện tượng lừa đảo ấy chị có thể cho em hỏi tài khoản này có hoạt động bình thường không ạ",
#     "dạ vâng số tài khoản không một không một không một một bảy bốn không bảy",
#     "một không một một bảy bốn không bảy",
#     "phan thị là",
#     "em là nguyễn văn trường",
#     "một sáu bốn một ạ",
#     "không ba ba ạ",
#     "sáu không ạ",
#     "vâng ạ em là ngân hàng agribank",
# ]
right_sentences_text = [
    "xin chào, tên tôi là đoàn vũ thuận",
    "căn cước số không hai bốn ",
    #"không một năm bốn ba sáu địa chỉ nhà tôi năm chín hai xẹt một đường nguyễn văn quá quận mười hai",
    "không một năm bốn ba sáu địa chỉ nhà tôi 592 đường nguyễn văn quá quận 12",
    "số điện thoại của tôi không chín không hai bảy hai bảy hai ba một",
    ]
right_sentences_text = [line.capitalize() for line in right_sentences_text]
    
text = " . ".join(right_sentences_text)
#print(text)
#text = text.upper()
#print(extract_customer_info(text))
#print(parse_name_entity(text))
vi_output = p.ner(text)
print(vi_output)

# customer_text_sum = ""
# for right_sen in right_sentences_text:
#     customer_text_sum += " " + process_audio_sentence(
#         right_sen, 2, call_id, customer_text_sum
#     )
