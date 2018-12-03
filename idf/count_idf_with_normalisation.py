import json
import pymorphy2

morph = pymorphy2.MorphAnalyzer()

with open('../plugin/idf.json') as f:
    not_normalised_idf = json.loads(f.read())

normalised_idf = dict()

for term, tf in not_normalised_idf.items():
    normal_form = morph.parse(term)[0].normal_form

    if normalised_idf.get(normal_form) is None:
        normalised_idf[normal_form] = int(not_normalised_idf[term])
    else:
        normalised_idf[normal_form] = normalised_idf[normal_form] + int(not_normalised_idf[term])


with open('../plugin/normalised_idf.json', 'w', encoding='utf-8') as fp:
    json.dump(normalised_idf, fp, ensure_ascii=False)
