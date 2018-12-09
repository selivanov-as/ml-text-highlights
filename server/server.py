import json
import time
from flask import Flask, request
import pymorphy2
import json
from pprint import pprint
import operator

with open('../normalized_idf/normalized_idf.json') as f:
    normalised_idf = json.loads(f.read())

with open("./stopwords.txt") as f:
    stop_words_list = f.readlines()

stop_words = {}
for x in stop_words_list:
    stop_words[x.strip()] = True

morph = pymorphy2.MorphAnalyzer()

app = Flask(__name__)


@app.route('/tf-idf', methods=['POST'])
def handleTF_IDF():
    words = json.loads(request.data)
    normalized_words = []
    results = []
    included_normal_forms = {}

    for i, word in enumerate(words):
        normalized_words.append(morph.parse(word)[0].normal_form)

    doc_length = len(normalized_words)
    for i, word in enumerate(normalized_words):
        if (word.isnumeric()): continue

        word_normal_form = morph.parse(word)[0].normal_form
        word_normal_form_idf = normalised_idf.get(word_normal_form)

        word_normal_form_exist = word_normal_form_idf is not None
        word_is_not_in_stop_words_list = stop_words.get(words[i]) is None and stop_words.get(word_normal_form) is None

        if word_normal_form_exist and word_is_not_in_stop_words_list:
            tf_idf_info = {
                'word': words[i],
                'tf_idf': normalized_words.count(word) / doc_length * 1000 / word_normal_form_idf,
                'tf': normalized_words.count(word),
                'doc_length': doc_length,
                'idf': word_normal_form_idf
            }

        elif not word_normal_form_exist:
            tf_idf_info = {
                'word': words[i],
                'tf_idf': 1337,
                'tf': normalized_words.count(word),
                'doc_length': doc_length,
                'idf': word_normal_form_idf
            }

        if included_normal_forms.get(word_normal_form) is None:
            results.append(tf_idf_info)
            included_normal_forms[word_normal_form] = True

    return json.dumps(sorted(results, key=operator.itemgetter('tf_idf'), reverse=True), ensure_ascii=False)
