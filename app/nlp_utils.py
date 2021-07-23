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


def parse_customer_info(p, sentence):
    # get POS
    sentence_pos = p.posdep(sentence.lower(), is_sent=True)

    # parse POS to capitalize private name
    name_entities = parse_senten_pos(sentence_pos)

    per_list, loc_list = parse_ner(p,name_entities)
    return per_list, loc_list


def parse_senten_pos(sentence):
    name_list = []
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
        
        i += 1

    return name_list

def parse_ner(p, name_entities):

    per_list = []
    loc_list = []
    for name in name_entities:
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
        if loc_parts != "" and  loc_parts not in loc_list:
            loc_list.append(loc_parts)
    return per_list, loc_list
