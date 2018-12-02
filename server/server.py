import json
import time
from flask import Flask, request
import pymorphy2
import json
from pprint import pprint

with open('../plugin/idf.json') as f:
    data = json.loads(f.read())

morph = pymorphy2.MorphAnalyzer()

app = Flask(__name__)

@app.route('/tf-idf', methods=['POST'])
def handleTF_IDF():

    words = json.loads(request.data)
    for word in words:
        print(morph.parse(word)[0].normal_form)
        pprint(data)

    return json.dumps(words)
