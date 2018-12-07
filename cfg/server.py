import json
import time
from entity_finder import find_entities
from flask import Flask, request
import pymorphy2
import json
from pprint import pprint

with open('data.json') as f:
    data = json.load(f)

morph = pymorphy2.MorphAnalyzer()

app = Flask(__name__)


@app.route('/cfg', methods=['POST'])
# def work_with_cfg():
#     if request.method == 'POST':
#         # print('raw input:', request.data, sep='\n')
#         texts = json.loads(request.data)
#         # print(text)
#         spans = []
#         for text in texts:
#             spans.append(find_entities(text))
#         assert len(texts) == len(spans), f'length of texts is{len(texts)} while length of spans is {len(spans)}'
#         # print(spans)
#         return json.dumps(spans)

@app.route('/tf-normalized_idf', methods=['POST'])
def handleTF_IDF():
    words = json.loads(request.data)
    for word in words:
        print(morph.parse(word)[0].normal_form)

    return json.dumps(words)
