import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
from trankit import Pipeline
p = Pipeline(lang="vietnamese",cache_dir='app/cache')



#read corpus
corpus = []
file = open('transcripts.txt', 'r', encoding="utf-8")
lines = file.readlines()
for line in lines:
    segments = line.split('        ')
    if len(segments) > 1:
        corpus.append(segments[1])
        #print(segments[1])

corpus  = " ".join(corpus)

#tokenizer
tokenized_doc = p.tokenize(corpus)

token_corpus = []
for sentence in tokenized_doc['sentences']:
    for token in sentence['tokens']:
        token_word = token['text'].replace(" ",'_')
        token_corpus.append(token_word)

token_corpus  = " ".join(token_corpus)

vectorizer = TfidfVectorizer()
tfIdf = vectorizer.fit_transform([token_corpus])
df = pd.DataFrame(tfIdf[0].T.todense(), index=vectorizer.get_feature_names(), columns=["TF-IDF"])
df = df.sort_values('TF-IDF', ascending=False)
print (df.head(30))
#print(tfIdf[0].T.todense())
print(df.loc['phan_thị'][0])
tfIdf_dict = df.to_dict()
print(tfIdf_dict)

# save to file
file = open('tfidf_dict.pkl', 'wb')
pickle.dump(tfIdf_dict['TF-IDF'], file)
file.close()

# open a file, where you stored the pickled data
file = open('tfidf_dict.pkl', 'rb')

# dump information to that file
tfidf_dict = pickle.load(file)

print(tfidf_dict['anh'])

# close the file
file.close()