import trankit

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

from trankit import Pipeline
p = Pipeline(lang='customized-ner', cache_dir='./save_dir')

text = 'em hôm qua chuyển tiền cho số tài khoản của phan thị là em nghi có hiện tượng lừa đảo'

vi_output = p.ner(text)
print(vi_output)