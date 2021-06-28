import re
from typing import Dict, List, Tuple

from trankit import Pipeline

from .config import settings
from .constant import (BAD_WORDS, ID_REGEX, ID_REGEX_OLD, NUMERIC_MAPPINGS,
                       PHONE_REGEX)

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
            if token["ner"] == "B-PER":
                name_list.append(token["text"])

            if "LOC" in token["ner"]:
                address_list.append(token["text"])

    return name_list, address_list


def num_mapping(text):
    for pattern, repl in NUMERIC_MAPPINGS.items():
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)

    return text


def extract_customer_info(text):
    """ Doing entities regconition """
    # name entity recoginition
    name_list, address_list = parse_name_entity(text)

    # parse cmnd, sdt
    id_number, phone_number = parse_id_phone_number(text)

    extract_info = {}
    extract_info["nameList"] = ",".join(name_list)
    extract_info["addressList"] = ",".join(address_list)
    extract_info["idNumber"] = id_number
    extract_info["phoneNumber"] = phone_number

    return extract_info


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

    # Remove all the words affect the pattern matching

    text = re.sub("|".join(BAD_WORDS), "", text)
    # for word in BAD_WORDS:
    #     text = re.sub(word, "", text)

    # print(f"start extracting from text: {text}")

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
    start, end = match.span()
    return text[start : end - 1]  # noqa: E203
