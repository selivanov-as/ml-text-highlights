import json
import pymorphy2

morph = pymorphy2.MorphAnalyzer()

with open("./1grams-3.txt") as f:
    content = f.readlines()
content = [x.strip() for x in content]

normalised_idf = dict()

print("Parsing has started!")
for raw in content:
    tf, word = raw.split('\t')

    if word == {}:
        continue

    word_normal_form = morph.parse(word)[0].normal_form
    if normalised_idf.get(word_normal_form) is None:
        normalised_idf[word_normal_form] = int(tf)
    else:
        normalised_idf[word_normal_form] = int(normalised_idf[word_normal_form]) + int(tf)

with open("./normalized_idf.json", 'w', encoding='utf-8') as fp:
    json.dump(normalised_idf, fp, ensure_ascii=False)

print("Parsing has finished!")
