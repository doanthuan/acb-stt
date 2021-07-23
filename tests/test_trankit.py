import pickle

DEBUG = True
if not DEBUG:
    from trankit import Pipeline
    p = Pipeline(lang="vietnamese",gpu=False, cache_dir='../app/cache')

bad_names = ['công an', 'hong', 'tám lăm', 'á', 'e', 'a', 'x', 'chi tiêu', 'kiều hối', 'en nờ']
bad_names_pattern = ['bên', 'chấm', 'tài khoản']

def is_valid_name(name):
    name = name.replace(' % ', ' ')
    name = name.replace(' %% ', ' ')
    if name in bad_names:
        return False
    
    for bname in bad_names_pattern:
        if bname in name:
            return False

    pronoun = ['anh', 'chị', 'a ']
    for n in pronoun:
        if name.find(n) == 0:
            return False

    return True


def is_name_exist(name, name_list):
    if name in name_list:
        return True
    for aname in name_list:
        if aname in name:
            return True
    return False


# #read corpus
# corpus = []
# file = open('acb-full-clean-4.txt', 'r', encoding="utf-8")
# lines = file.readlines()
# for line in lines:
#     segments = line.split('	')
#     if len(segments) > 1 and segments[1] != "":
#         corpus.append(segments[1])
#         #print(segments[1])

# assert(len(corpus) > 0) , "Parse dataset error!!!"
# #corpus  = " ".join(corpus)
# corpus_pos = []
# for sentence in corpus:
#     if isinstance(sentence, str) and sentence != "":
#         try:
#             sentence_pos = p.posdep(sentence.lower(), is_sent=True)
#             corpus_pos.append(sentence_pos)
#         except:
#             continue

# # save to file
# file = open('corpus_pos.pkl', 'wb')
# pickle.dump(corpus_pos, file)
# file.close()
# print(corpus_pos)


### CONTINUE
file = open('corpus_pos.pkl', 'rb')
corpus_pos = pickle.load(file)
file.close()

name_list = []
sentences = []
for sentence in corpus_pos:
    # if "công an" in sentence['text']:
    #     print(sentence['tokens'])
        #break

    i = 0
    while( i < len (sentence['tokens'])):
        
        token = sentence['tokens'][i]
        if i < len(sentence['tokens']) -1: 
            next_token = sentence['tokens'][i+1]
        else:
            next_token = None

        full_name = ""
        if token['xpos'] == 'Np' and token['deprel'] not in ['nsubj','obl','obj', 'conj']:
            full_name = token['text']
            if next_token and ( next_token['xpos'] == 'Np' or
                ( next_token['upos'] == 'NOUN' and next_token['deprel'] == 'compound') or 
                (token['deprel'] == 'root' and next_token['upos'] == 'CCONJ') ):
                full_name += " % " + next_token['text']
            
            if is_valid_name(full_name) and len(full_name.split(" ")) > 1:
                name_list.append(full_name)
                i += 1
                if '%' in full_name:
                    i += 1
                continue

        if token['upos'] == 'NOUN' and token['xpos'] != 'Nc' and token['deprel'] not in ['nsubj','obl','obj','compound', 'nmod']:
            if next_token and  next_token['xpos'] == 'Np' and next_token['deprel'] == 'compound':
                full_name = token['text'] + " %% " + next_token['text']
                if i < len(sentence['tokens']) - 2: 
                    next_next_token = sentence['tokens'][i+2]
                    if next_next_token['xpos'] == 'Np' and next_next_token['deprel'] == 'compound':
                        full_name = token['text'] + " %% " + next_token['text'] + " %% " + next_next_token['text']
                        i += 1

                if is_valid_name(full_name):
                    name_list.append(full_name)
                    i += 2
                    continue

        # if token['upos'] == 'NOUN' and token['xpos'] != 'Nc' and token['deprel'] == 'root':
        #     if next_token and  next_token['upos'] == 'NOUN' and next_token['deprel'] == 'compound':
        #         full_name = token['text'] + " %%% " + next_token['text']

        #         if is_valid_name(full_name):
        #             name_list.append(full_name)
        #             i += 2
        #             continue
        

        i += 1

if DEBUG:
    print("\n".join(name_list))

if not DEBUG:
    per_list = []
    loc_list = []
    for name in name_list:
        name = name.replace(' %% ',' ')
        name = name.replace(' % ',' ')
        name_str = " ".join([n.capitalize() for n in name.split(' ')])
        output = p.ner(name_str, is_sent=True)
        name_parts = ""
        loc_parts = ""
        for token in output['tokens']:
            if 'PER' in token['ner']:
                name_parts += " " + token['text']
            if 'LOC' in token['ner']:
                loc_parts += " " + token['text']
        if name_parts != "" and name_parts not in per_list:
            per_list.append(name_parts)
            print(f'PERSON: {name_parts}')
        if loc_parts != "" and  loc_parts not in loc_list:
            loc_list.append(loc_parts)
            print(f'LOCATION: {loc_parts}')
