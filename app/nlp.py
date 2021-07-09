import logging
import re
from typing import Dict, List, Tuple, Union

from trankit import Pipeline

from .config import settings
from .constant import (BAD_NAMES, BAD_WORDS, DIGITS, ID_REGEX, ID_REGEX_OLD,
                       NUMERIC_MAPPINGS, PHONE_REGEX)

logger = logging.getLogger(__name__)
# p = Pipeline(lang="vietnamese", gpu=False, cache_dir=settings.CACHE_DIR)
p = Pipeline(lang="customized-ner", gpu=False, cache_dir=settings.CACHE_DIR)


def parse_name_entity(text: str) -> Tuple[List[str], List[str]]:
    text = num_mapping(text)
    # bad_words = [r'\n', 'ạ']
    # text = re.sub('|'.join(bad_words), " ", text)
    # words = [word.capitalize() for word in text.split(' ')]
    # text = ' '.join(words)

    # name entity recognition
    vi_output = p.ner(text)
    name_list = []
    address_list = []

    # token_list = vi_output["sentences"][0]["tokens"]
    sentences = vi_output["sentences"]
    for sentence in sentences:
        for token in sentence["tokens"]:
            if "PER" in token["ner"]:
                name_list.append(token["text"])

            if "LOC" in token["ner"]:
                address_list.append(token["text"])

    return name_list, address_list


def extract_info_from_ner(ner_output: Dict, tag: str) -> List[str]:
    res = []
    sentences = ner_output["sentences"]
    for sentence in sentences:
        single_ent = []
        for token in sentence["tokens"]:
            if tag in token["ner"]:
                single_ent.append(token["text"])
        if len(single_ent) > 0:
            res.append(" ".join(single_ent))
    return res


def num_mapping(text):
    for pattern, repl in NUMERIC_MAPPINGS.items():
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)

    return text


def extract_customer_info(current_text: Union[str, Dict], criteria: Dict) -> Dict:
    if isinstance(current_text, str):
        return extract_customer_info_str(current_text, criteria)
    return extract_customer_info_dict(current_text, criteria)


def extract_customer_info_dict(text: Dict, criteria) -> Dict:
    res = {
        "nameList": "",
        "addressList": "",
        "idNumber": "",
        "phoneNumber": "",
    }

    if criteria.get("detect_name") is True:
        res["nameList"] = extract_customer_info_str(text["names"], criteria)["nameList"]

    if criteria.get("detect_address") is True:
        res["addressList"] = extract_customer_info_str(text["addresses"], criteria)[
            "addressList"
        ]

    if criteria.get("detect_id") is True:
        res["idNumber"] = extract_customer_info_str(text["id"], criteria)["idNumber"]

    if criteria.get("detect_phone") is True:
        res["phoneNumber"] = extract_customer_info_str(text["phone"], criteria)[
            "phoneNumber"
        ]

    return res


def is_blacklist(text: str, blacklist: List[str]) -> bool:
    for word in blacklist:
        if word in text:
            return True
    return False


def extract_customer_info_str(text: str, criteria: Dict) -> Dict:
    """Doing entities regconition"""
    customer_info = {
        "nameList": "",
        "addressList": "",
        "idNumber": "",
        "phoneNumber": "",
    }
    if not text:
        logger.warning("input text is empty")
        return customer_info

    # Extract customer info. To do that more accurately, text needs
    # to be preprocess such as convert to number, remove bad words that affects
    # the pattern matching
    print(f'Scanning Named Identity for text="{text}"')

    ner_output = ""
    if criteria.get("detect_name") is True:
        if ner_output == "":
            ner_output = p.ner(text)
        names = extract_info_from_ner(ner_output, tag="PER")
        names = [name for name in names if not is_blacklist(name, BAD_NAMES)]
        customer_info["nameList"] = ",".join(names)

    if criteria.get("detect_address") is True:
        text = process_address_input(text)
        ner_output = p.ner(text)
        addresses = extract_info_from_ner(ner_output, tag="LOC")
        addresses = [addr for addr in addresses if not is_blacklist(addr, BAD_NAMES)]
        customer_info["addressList"] = ",".join(addresses)

    text = num_mapping(text)
    text = re.sub("|".join(BAD_WORDS), "", text)
    text = expand_number(text)
    text = re.sub(r"\s", "", text)
    print(f'Scanning ID & Phone number for text="{text}"')
    if criteria.get("detect_id") is True:
        customer_info["idNumber"] = extract_info(ID_REGEX, text)
        if customer_info["idNumber"] == "":
            customer_info["idNumber"] = extract_info(ID_REGEX_OLD, text)

            # this can be tricky as the old-id-pattern matches can contain
            # non-numeric character. It's needed to remove them
            if len(customer_info["idNumber"]) > 9:
                customer_info["idNumber"] = customer_info["idNumber"][:9]

    if criteria.get("detect_phone") is True:
        print(f"Detect phone: text={text} ...")
        customer_info["phoneNumber"] = extract_info(PHONE_REGEX, text)

    return customer_info


def process_address_input(in_text: str) -> str:
    # TODO: more cases to handle
    in_text = num_mapping(in_text)
    for word in [" xẹt ", " xuyệc ", " xuyệt "]:
        in_text = in_text.replace(word, " / ")
    return in_text


def is_digit(word):
    return word in DIGITS


def expand_number(text):
    if "số" not in text:
        return text

    words = text.split(" ")
    res = []
    i = 0
    words_len = len(words)
    while i < words_len:
        # pattern like: ba số không = 000
        if (
            (i < words_len - 2)
            and is_digit(words[i])
            and (words[i + 1] == "số")
            and is_digit(words[i + 2])
        ):
            res.append(int(words[i]) * words[i + 2])
            i += 3
        else:
            res.append(words[i])
            i += 1
    return " ".join(res)


def extract_identity_info(text: str) -> Dict:
    name_list, address_list = parse_name_entity(text)
    id_number, phone_number = parse_id_phone_number(text)
    return {
        "name": name_list,
        "address": address_list,
        "id_number": id_number,
        "phone_number": phone_number,
    }


# from vietnam_number import w2n_single, w2n_couple
def parse_id_phone_number(text) -> Tuple[str, str]:

    text = num_mapping(text)
    text = re.sub("|".join(BAD_WORDS), "", text)

    # Extract the identity information by pattern matching
    # adding a single non-numeric character to avoid the case that
    # longer pattern would cover the shorter pattern leads to wrong extraction
    id_number = extract_info(ID_REGEX, text)
    if id_number == "":
        id_number = extract_info(ID_REGEX_OLD, text)

    phone_number = extract_info(PHONE_REGEX, text)

    return id_number, phone_number


def extract_info(regex: str, text: str) -> str:
    p = re.compile(regex)
    match = p.search(text)
    if match is None:
        return ""

    # remove last non-numeric character
    return match.group()
    # start, end = match.span()
    # return text[start : end - 1]  # noqa: E203
