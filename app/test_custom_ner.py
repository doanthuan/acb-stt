from trankit import Pipeline
from nlp import *

# trankit.download_missing_files(
# 	category='customized-ner',
# 	save_dir='./save_dir',
# 	embedding_name='xlm-roberta-base',
# 	language='vietnamese'
# )

# trankit.verify_customized_pipeline(
#     category='customized-ner', # pipeline category
#     save_dir='./save_dir', # directory used for saving models in previous steps
#     embedding_name='xlm-roberta-base' # embedding version that we use for training our customized pipeline, by default, it is `xlm-roberta-base`
# )

p = Pipeline(lang="customized-ner", cache_dir="./save_dir")

#text = "em hôm qua chuyển tiền cho số tài khoản của phan thị là em nghi có hiện tượng lừa đảo"
#text = "chủ tài khoản nguyễn thị trà linh tài khoản một ba"
text = "chủ tài khoản trần thị ngọc nga tài khoản một ba"
vi_output = p.ner(text, is_sent=True)
print(vi_output)

# criteria = {}
# criteria["detect_name"] = True
# criteria["detect_phone"] = True
# names = extract_info_from_ner(vi_output, tag="PER")
# #names = ['nguyễn thị trà linh']
# for name in names:
#     if is_blacklist(name, BAD_NAMES):
#         print("is_blacklist")
#         print(name)
#     else:
#         print(f"ok name:{name}")
# #names = [name for name in names if not is_blacklist(name, BAD_NAMES)]
# #customer_info = extract_customer_info_str(text, criteria=criteria)
# print(names)


