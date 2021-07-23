from trankit import Pipeline
p = Pipeline(lang="vietnamese",gpu=False, cache_dir='../app/cache')



text = 'EM HÔM QUA CHUYỂN TIỀN CHO SỐ TÀI KHOẢN CỦA PHAN THỊ LÀ EM NGHI CÓ HIỆN TƯỢNG LỪA ĐẢO ẤY CHỊ CÓ THỂ CHO EM HỎI TÀI KHOẢN NÀY CÓ HOẠT ĐỘNG BÌNH THƯỜNG KHÔNG Ạ'
per_list, loc_list = parse_customer_info(text)
print(f'PERSON:{",".join(per_list)}')
print(f'LOCATION:{",".join(loc_list)}')