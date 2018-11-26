import json
from entity_finder import find_entities
from flask import Flask, request

app = Flask(__name__)


@app.route('/cfg', methods = ['POST'])
def work_with_cfg():
	if request.method == 'POST':
		text = request.data.decode()
		#print(text)
		spans = find_entities(text)
		#print(spans)
		return json.dumps(spans)