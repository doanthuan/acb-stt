from trankit import Pipeline
p = Pipeline(lang="vietnamese",gpu=False, cache_dir='app/cache')

text = 'CÒN ĐỊA CHỈ CỦA MÌNH THÌ VẪN LÀ HỒ VĂN HUÊ CŨ TRÊN CÁI ĐỊA CHỈ ĐĂNG KÝ VỚI NGÂN HÀNG ĐÓ HẢ LÀ CÁI THÔNG TIN CŨ MÌNH LÀ CHƯA THAY ĐỔI'
text = text.lower()

vi_output = p.ner(text, is_sent=True)
sentence_pos = p.posdep(text, is_sent=True)
print(sentence_pos)