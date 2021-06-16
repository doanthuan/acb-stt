from trankit import Pipeline

from config import settings

p = Pipeline(lang="vietnamese", gpu=True, cache_dir=settings.CACHE_DIR)

#text = "120 đường hai bà trưng quận 3"
right_sentences_text = [
    "chị cho em hỏi chút được không ạ",
    "em hôm qua chuyển tiền cho số tài khoản của phan thị là em nghi có hiện tượng lừa đảo ấy chị có thể cho em hỏi tài khoản này có hoạt động bình thường không ạ",
    "dạ vâng số tài khoản không một không một không một một bảy bốn không bảy",
    "một không một một bảy bốn không bảy",
    "phan thị là",
    "em là nguyễn văn trưởng",
    "một sáu bốn một ạ",
    "không ba ba ạ",
    "sáu không ạ",
    "vâng ạ em là ngân hàng agribank",
]

#text = " . ".join(right_sentences_text)
#text = text.upper()
text = "em là nguyễn văn trường"
vi_output = p.ner(text)
#vi_output = p.ner("TÔI TÊN LÀ KHỔNG VĂN CHIẾN ĐỊA CHỈ NHÀ Ở")


token_list = vi_output["sentences"][0]["tokens"]
print(token_list)