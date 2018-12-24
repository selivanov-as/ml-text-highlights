import json
from flask import Flask, request
from server.tf_idf_normalized import tf_idf_normalized

app = Flask(__name__)


@app.route('/tf-idf', methods=['POST'])
def handleTF_IDF():
    words = json.loads(request.data)
    result = tf_idf_normalized(words)

    return json.dumps(sorted(result, key=operator.itemgetter('tf_idf'), reverse=True), ensure_ascii=False)
