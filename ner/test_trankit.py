from trankit import Pipeline

p = Pipeline(lang="vietnamese", cache_dir='../cache')

#text = 'tôi tên là đoàn vũ thuận'
text = 'số tài khoản của đoàn vũ thuận em nghi có hiện tượng lừa đảo ấy'

tokenized_doc = p.ner(text)

print(tokenized_doc)