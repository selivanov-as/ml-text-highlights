import json
import time
from entity_finder import find_entities
from flask import Flask, request

app = Flask(__name__)


def find_in_texts(texts, dlm=' '):
    joined = dlm.join(texts)
    borders = []
    end = -len(dlm)
    for text in texts:
        beg = end + len(dlm)
        end = beg + len(text)
        borders.append((beg, end))
        
    assert len(borders) == len(texts), (len(borders), len(texts))
    assert borders[-1][1] == len(joined), (borders[-1][1], len(joined))
    
    begin = time.perf_counter()
    spans = find_entities(joined)
    cfg_time = time.perf_counter() - begin
    print(f'cfg_time: {cfg_time} s')
    
    cur_ind = 0
    grouped_spans = []
    for (beg, end) in borders:
        start_ind = cur_ind
        while spans[cur_ind][1] < end and cur_ind + 1 < len(spans):
            cur_ind += 1
        cur_spans = spans[start_ind : cur_ind]
        if spans[cur_ind][0] < end:  # span is divided between text nodes
            cur_spans.append((spans[cur_ind][0], end))
        cur_spans = [tuple(max(0, x - beg) for x in span)
                            for span in cur_spans]
        grouped_spans.append(cur_spans)
    
    assert len(texts) == len(grouped_spans), (len(texts), len(grouped_spans))
    return grouped_spans


@app.route('/cfg', methods = ['POST'])
def work_with_cfg():
    assert request.method == 'POST'
    begin = time.perf_counter()
    texts = json.loads(request.data)
    #print(texts)
    spans = find_in_texts(texts)
    #print(spans)
    overall_time = time.perf_counter() - begin
    print(f'overall time: {overall_time} s')
    return json.dumps(spans)
