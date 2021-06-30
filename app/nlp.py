import logging
import re
from typing import Dict, List, Tuple, Union

from trankit import Pipeline

from .config import settings
from .constant import (BAD_WORDS, ID_REGEX, ID_REGEX_OLD, NUMERIC_MAPPINGS,
                       PHONE_REGEX)

logger = logging.getLogger(__name__)
p = Pipeline(lang="vietnamese", gpu=False, cache_dir=settings.CACHE_DIR)


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
        for token in sentence["tokens"]:
            if tag in token["ner"]:
                res.append(token["text"])
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


def extract_customer_info_str(text: str, criteria: Dict) -> Dict:
    """ Doing entities regconition """
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
    text = num_mapping(text)
    print(f'Scanning Named Identity for text="{text}"')

    ner_output = ""
    if criteria.get("detect_name") is True:
        if ner_output == "":
            ner_output = p.ner(text)
        names = extract_info_from_ner(ner_output, tag="PER")
        customer_info["nameList"] = ",".join(names)

    if criteria.get("detect_address") is True:
        if ner_output == "":
            ner_output = p.ner(text)
        addresses = extract_info_from_ner(ner_output, tag="LOC")
        customer_info["addressList"] = ",".join(addresses)

    text = re.sub("|".join(BAD_WORDS), "", text)
    print(f'Scanning ID & Phone number for text="{text}"')
    if criteria.get("detect_id") is True:
        customer_info["idNumber"] = extract_info(ID_REGEX, text)
        if customer_info["idNumber"] == "":
            customer_info["idNumber"] = extract_info(ID_REGEX_OLD, text)

    if criteria.get("detect_phone") is True:
        customer_info["phoneNumber"] = extract_info(PHONE_REGEX, text)

    return customer_info


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
