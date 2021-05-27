from trankit import Pipeline

from config import settings

p = Pipeline(lang="vietnamese", gpu=False, cache_dir=settings.CACHE_DIR)

text = "592 đường nguyễn văn quá quận 12"

text = text.upper()
vi_output = p.ner(text)

token_list = vi_output["sentences"][0]["tokens"]
print(vi_output)