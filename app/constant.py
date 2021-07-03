# words that should not be included in the text when doing entities recognition
# the leading space is used to make sure that these are single words
# order does matter. So, we need to replace space after removing all other
# bad-words
BAD_WORDS = [" òi", " ồi", " em", " a", " ạ", " à", " á", " ở", " e", "rồi", "y"]

# regex to match phone number in VN (as standard)
PHONE_REGEX = r"(0?)(3[2-9]|5[6|8|9]|7[0|6-9]|8[0-6|8|9]|9[0-4|6-9])\d{7,8}"

# regex to match ID number (new format)
# ID_REGEX = r"0([0-8]\d|9[0-6])\d{9}[^\d]"
ID_REGEX = r"0([0-8]\d|9[0-6])\d{9}"

# regex to match ID number (old format)
# ID_REGEX_OLD = r"(0[1-8]\d|09[0-2]|[1-2]\d{2}|3[0-8]\d)\d{6}[^\d]"
ID_REGEX_OLD = r"(0[1-8]\d|09[0-2]|[1-2]\d{2}|3[0-8]\d)\d{6}([^\d]|$)"

# add leading space to avoid replace the match inside of the words such as agribank
NUMERIC_MAPPINGS = {
    "không": "0",
    "một": "1",
    "hai": "2",
    "ba": "3",
    "bốn": "4",
    "năm": "5",
    "lăm": "5",
    "sáu": "6",
    "bảy": "7",
    "tám": "8",
    "chín": "9",
}

DIGITS = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
