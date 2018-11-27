import json
import time
from entity_finder import find_entities
from flask import Flask, request

app = Flask(__name__)


@app.route('/cfg', methods = ['POST'])
def work_with_cfg():
	if request.method == 'POST':
		#print('raw input:', request.data, sep='\n')
		texts = json.loads(request.data)
		#print(text)
		spans = []
		for text in texts:
			spans.append(find_entities(text))
		assert len(texts) == len(spans), f'length of texts is{len(texts)} while length of spans is {len(spans)}'
		print(spans)
		return json.dumps(spans)