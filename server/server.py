import json
import time
from flask import Flask, request
import pymorphy2
import json
from pprint import pprint

with open('../normalized_idf/normalized_idf.json') as f:
    normalised_idf = json.loads(f.read())

morph = pymorphy2.MorphAnalyzer()

app = Flask(__name__)


@app.route('/tf-idf', methods=['POST'])
def handleTF_IDF():
    tf_idf = dict()

    words = json.loads(request.data)
    normalized_words = []
    for i, word in enumerate(words):
        normalized_words.append(morph.parse(word)[0].normal_form)

    for i, word in enumerate(normalized_words):
        word_normal_form = morph.parse(word)[0].normal_form
        word_normal_form_idf = normalised_idf.get(word_normal_form)

        if word_normal_form_idf is not None:
            tf_idf[words[i]] = [(normalized_words.count(word) / len(normalized_words) * 1000) / word_normal_form_idf,
                                normalized_words.count(word), word_normal_form_idf]

    return json.dumps(tf_idf, ensure_ascii=False)
