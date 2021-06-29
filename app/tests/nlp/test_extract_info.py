from trankit import Pipeline

from app.models.ner import NerType
from app.nlp import extract_customer_info
from app.tests.utils import extract_tokens


def test_recognize_id():
    in_text = """dạ không hai năm\n
                bảy hai chín\n
                bốn không á chín\n
    """
    cust_info = extract_customer_info(
        in_text,
        criteria={
            "detect_name": False,
            "detect_address": False,
            "detect_id": True,
            "detect_phone": False,
        },
    )
    assert cust_info["idNumber"] == "025729409"


def test_recognize_id_2():
    in_text = """một sáu bốn một ạ ạ\n
                không ba ba ạ ạ\n
                sáu không ạ ạ\n
                cảm ơn anh cung cấp thông tin
    """
    cust_info = extract_customer_info(
        in_text,
        criteria={
            "detect_name": False,
            "detect_address": False,
            "detect_id": True,
            "detect_phone": False,
        },
    )
    assert cust_info["idNumber"] == "164103360"


def test_recognize_id_3():
    in_text = """một chín bảy á ba sáu á năm ba sáu tám
    """
    cust_info = extract_customer_info(
        in_text,
        criteria={
            "detect_name": False,
            "detect_address": False,
            "detect_id": True,
            "detect_phone": False,
        },
    )
    assert cust_info["idNumber"] == "197365368"


def test_recognize_name():
    in_text = """em là nguyễn văn trường ạ ạ
    """
    cust_info = extract_customer_info(
        in_text,
        criteria={
            "detect_name": True,
            "detect_address": False,
            "detect_id": False,
            "detect_phone": False,
        },
    )
    assert "nguyễn văn trường" in cust_info["nameList"]


def test_recognize_name_2():
    in_text = """dạ lê thảo phúc
    """
    cust_info = extract_customer_info(
        in_text,
        criteria={
            "detect_name": True,
            "detect_address": False,
            "detect_id": False,
            "detect_phone": False,
        },
    )
    assert "lê thảo phúc" in cust_info["nameList"]


def test_recognize_name_3():
    in_text = """dạ phùng thị khánh trang
    """
    cust_info = extract_customer_info(
        in_text,
        criteria={
            "detect_name": True,
            "detect_address": False,
            "detect_id": False,
            "detect_phone": False,
        },
    )
    assert "phùng thị khánh trang" in cust_info["nameList"]

def test_recognize_name_4():
    in_text = """dạ rồi cám ơn chị trang """
    cust_info = extract_customer_info(
        in_text,
        criteria={
            "detect_name": True,
            "detect_address": False,
            "detect_id": False,
            "detect_phone": False,
        },
    )
    assert "trang" in cust_info["nameList"]

def test_ner(pipeline: Pipeline):
    right_sentences_text = [
        "xin chào, tên tôi là đoàn vũ thuận",
        "căn cước số không hai bốn ",
        # "không một năm bốn ba sáu địa chỉ nhà tôi năm chín hai xẹt một đường nguyễn văn quá quận mười hai",
        "không một năm bốn ba sáu địa chỉ nhà tôi 592 đường nguyễn văn quá quận 12",
        "số điện thoại của tôi không chín không hai bảy hai bảy hai ba một",
    ]
    processed_text = []
    for line in right_sentences_text:
        processed_text.append(" ".join([word.capitalize() for word in line.split()]))
    # right_sentences_text = [line.capitalize() for line in right_sentences_text]

    text = " . ".join(processed_text)
    # print(text)
    # text = text.upper()
    # print(extract_customer_info(text))
    # print(parse_name_entity(text))
    vi_output = pipeline.ner(text)
    print(vi_output)

    person_info = extract_tokens(vi_output, [NerType.PERSON])
    assert "Đoàn Vũ Thuận" in person_info

    loc = extract_tokens(vi_output, [NerType.I_LOCATION, NerType.B_LOCATION])
    assert "592 Đường Nguyễn Văn Quá Quận 12" in " ".join(loc)


# customer_text_sum = ""
# for right_sen in right_sentences_text:
#     customer_text_sum += " " + process_audio_sentence(
#         right_sen, 2, call_id, customer_text_sum
#     )
