# words that should not be included in the text when doing entities recognition
BAD_WORDS = [r"\s", "ạ", "dạ", "rồi"]

# regex to match phone number in VN (as standard)
PHONE_REGEX = r"(0?)(3[2-9]|5[6|8|9]|7[0|6-9]|8[0-6|8|9]|9[0-4|6-9])\d{7,8}[^\d]"

# regex to match ID number (new format)
ID_REGEX = r"0?([0-8]\d|9[0-6])\d{9}[^\d]"

# regex to match ID number (old format)
ID_REGEX_OLD = r"(0?[1-8]\d|09[0-25]|[1-2]\d{2}|3[0-8]\d)\d{6}[^\d]"

# add leading space to avoid replace the match inside of the words such as agribank
NUMERIC_MAPPINGS = {
    " không": " 0",
    " một": " 1",
    " hai": " 2",
    " ba": " 3",
    " bốn": " 4",
    " năm": " 5",
    " lăm": " 5",
    " sáu": " 6",
    " bảy": " 7",
    " tám": " 8",
    " chín": " 9",
}
