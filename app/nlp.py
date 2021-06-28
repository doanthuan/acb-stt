import logging
import re
from typing import Dict, List, Tuple

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


def extract_customer_info(text: str, criteria: Dict):
    """ Doing entities regconition """
    customer_info = {
        "nameList": "",
        "addressList": "",
        "idNumber": "",
        "phoneNumber": "",
    }

    # Extract customer info. To do that more accurately, text needs
    # to be preprocess such as convert to number, remove bad words that affects
    # the pattern matching
    text = num_mapping(text)

    try:
        ner_output = p.ner(text)
    except Exception as e:
        logger.error(f"Cannot do NER: text={text} criteria={criteria}")
        raise e
    if criteria.get("detect_name") is True:
        names = extract_info_from_ner(ner_output, tag="PER")
        customer_info["nameList"] = ",".join(names)

    if criteria.get("detect_address") is True:
        addresses = extract_info_from_ner(ner_output, tag="LOC")
        customer_info["addressList"] = ",".join(addresses)

    text = re.sub("|".join(BAD_WORDS), "", text)
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