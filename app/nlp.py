import logging
import re
from typing import Dict, List, Tuple, Union

from trankit import Pipeline

from .config import settings
from .constant import (ACC_NO_REGEX, BAD_NAMES, BAD_WORDS, CARD_NO_REGEX,
                       DIGITS, ID_REGEX, ID_REGEX_OLD, NUMERIC_MAPPINGS,
                       PHONE_REGEX)

logger = logging.getLogger(__name__)
p = Pipeline(lang="vietnamese", gpu=False, cache_dir=settings.CACHE_DIR)
# p = Pipeline(lang="customized-ner", gpu=False, cache_dir=settings.CACHE_DIR)


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
    #  sentences = ner_output["sentences"]
    sentences = [ner_output]
    for sentence in sentences:
        single_ent = []
        is_name = False
        is_name_ok = False
        for token in sentence["tokens"]:
            if tag in token["ner"]:
                is_name = True
                logger.info(f'tag={token["ner"]} text={token["text"]}')
                if (
                    (("B-" + tag) == token["ner"])
                    or (("E-" + tag) == token["ner"])  # noqa: W503
                    or (("S-" + tag) == token["ner"])  # noqa: W503
                ):
                    is_name_ok = True
                single_ent.append(token["text"])
            else:
                if is_name:
                    break
        single_ent = " ".join(single_ent)
        names = single_ent.split(" ")

        if (is_name_ok and len(names) > 1) or (len(names) > 2 and len(names) <= 4):
            res.append(single_ent)
    logger.info(f"tag={tag} result={res}")
    return res


def num_mapping(text) -> str:
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
        "accNumber": "",
        "cardNumber": "",
    }

    if criteria.get("detect_name") is True:
        ner_result = extract_customer_info_str(text["names"], criteria)
        logger.info(f"ner_result={ner_result}")
        res["nameList"] = ner_result["nameList"]

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

    if criteria.get("detect_card_no") is True:
        res["cardNumber"] = extract_customer_info_str(text["card_no"], criteria)[
            "cardNumber"
        ]

    if criteria.get("detect_acc_no") is True:
        res["accNumber"] = extract_customer_info_str(text["acc_no"], criteria)[
            "accNumber"
        ]

    return res


def is_blacklist(text: str, blacklist: List[str]) -> bool:
    for word in blacklist:
        if word in text:
            return True
    return False


def is_valid_name(text: str):
    txts = text.strip().split(" ")
    if len(txts) > 1 and len(txts) < 5:
        return True
    return False


def extract_customer_info_str(text: str, criteria: Dict) -> Dict[str, str]:
    """Doing entities regconition"""
    customer_info = {
        "nameList": "",
        "addressList": "",
        "idNumber": "",
        "phoneNumber": "",
        "cardNumber": "",
        "accNumber": "",
    }
    if not text:
        logger.warning("input text is empty")
        return customer_info

    # Extract customer info. To do that more accurately, text needs
    # to be preprocess such as convert to number, remove bad words that affects
    # the pattern matching
    logger.info(f'Scanning Named Identity for text="{text}"')

    ner_output = ""
    if criteria.get("detect_name") is True:
        ner_output = p.ner(normalize_name(text), is_sent=True)
        names = extract_info_from_ner(ner_output, tag="PER")
        # names = [name for name in names if is_valid_name(name)]
        names = [name for name in names if not is_blacklist(name, BAD_NAMES)]
        customer_info["nameList"] = ",".join(names)

    if criteria.get("detect_address") is True:
        text = process_address_input(text)
        ner_output = p.ner(normalize_name(text), is_sent=True)
        addresses = extract_info_from_ner(ner_output, tag="LOC")
        # addresses = [addr for addr in addresses if is_valid_name(addr)]
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
        # customer_info["idNumber"] = re.sub("\w", "", customer_info["idNumber"]

    if criteria.get("detect_phone") is True:
        customer_info["phoneNumber"] = extract_info(PHONE_REGEX, text)

    if criteria.get("detect_acc_no") is True:
        customer_info["accNumber"] = extract_info(ACC_NO_REGEX, text)

    if criteria.get("detect_card_no") is True:
        customer_info["cardNumber"] = extract_info(CARD_NO_REGEX, text)

    return customer_info


def process_address_input(in_text: str) -> str:
    # TODO: more cases to handle
    in_text = num_mapping(in_text)
    for word in [" xẹt ", " xuyệc ", " xuyệt "]:
        in_text = in_text.replace(word, " / ")
    return in_text


def is_digit(word) -> bool:
    return word in DIGITS


def expand_number(text) -> str:
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
            and is_digit(words[i])  # noqa: W503
            and (words[i + 1] == "số")  # noqa: W503
            and is_digit(words[i + 2])  # noqa: W503
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

    res = match.group()
    logger.debug(f"Found text={res} with pattern={regex}")

    # Remove non-digit character
    res = re.sub(r"[^0-9]", "", res)
    return res


def capitalize(text: str) -> str:
    return " ".join(w.capitalize() for w in text.split(" "))


def normalize_name(txt: str) -> str:
    # always enable sentence-mode when doing normalize name
    res = p.posdep(txt, is_sent=True)
    sent = []
    for word in res["tokens"]:
        sent.append(
            capitalize(word["text"]) if word["upos"] in ["PROPN"] else word["text"]
        )
    return " ".join(sent)
