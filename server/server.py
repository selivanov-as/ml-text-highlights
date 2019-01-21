import json
import operator
import string
import time
from pprint import pprint

import pymorphy2
from flask import Flask, request

from entity_finder import find_entities


THR = 0.25
SHARE = 0.3
PUNCTUATION = string.punctuation + "–—‒"

with open('../normalized_idf/normalized_idf.json') as f:
    normalised_idf = json.loads(f.read())

with open("./stopwords.txt") as f:
    stop_words_list = f.readlines()

with open("./norms_cbow_base.json") as f:
    vector_norms = json.load(f)

stop_words = {}
for x in stop_words_list:
    stop_words[x.strip()] = True

morph = pymorphy2.MorphAnalyzer()

app = Flask(__name__)


def find_with_cfg_in_texts(texts, dlm=' '):
    joined = dlm.join(texts)
    borders = []
    end = -len(dlm)
    for text in texts:
        beg = end + len(dlm)
        end = beg + len(text)
        borders.append((beg, end))
        
    assert len(borders) == len(texts), (len(borders), len(texts))
    assert borders[-1][1] == len(joined), (borders[-1][1], len(joined))
    
    #begin = time.perf_counter()
    spans = find_entities(joined)
    #cfg_time = time.perf_counter() - begin
    #print(f'cfg_time: {cfg_time} s')
    
    cur_ind = 0
    grouped_spans = []
    
    for (beg, end) in borders:
        start_ind = cur_ind
        while cur_ind < len(spans) and spans[cur_ind][1] < end:
            cur_ind += 1
        cur_spans = spans[start_ind : cur_ind]
        if cur_ind < len(spans) and spans[cur_ind][0] < end:  # span is divided between text nodes
            cur_spans.append((spans[cur_ind][0], end))
        cur_spans = [tuple(max(0, x - beg) for x in span)
                            for span in cur_spans]
        grouped_spans.append(cur_spans)
    
    assert len(texts) == len(grouped_spans), (len(texts), len(grouped_spans))
    return grouped_spans


@app.route('/cfg', methods = ['POST'])
def work_with_cfg():
    #begin = time.perf_counter()
    input = json.loads(request.data)
    texts = [x['text'] for x in input]
    spans = find_with_cfg_in_texts(texts)
    #overall_time = time.perf_counter() - begin
    #print(f'overall time: {overall_time} s')
    return json.dumps(spans)


def input_to_words(input):
    texts = [x['text'] for x in input]
    return [word for word in
                (token.strip(PUNCTUATION)
                 for text in texts
                 for token in text.split())
                if word]


def important_words_to_spans(important_words, input):
    grouped_spans = []
    for node in input:
        cur_pos = 0
        text = node['text']
        cur_spans = []
        for word in text.split():
            if word.strip(PUNCTUATION) in important_words:
                beg = text.find(word, cur_pos)
                cur_pos = end = beg + len(word)
                cur_spans.append((beg, end))
            else:
                cur_pos += len(word) + 1
        grouped_spans.append(cur_spans)
    return grouped_spans


def sorted_tfidfs_to_spans(sorted_tfidfs, input):
    n_important = int(len(sorted_tfidfs) * SHARE)
    important_words = {tf_idf_info['word']
                       for tf_idf_info in sorted_tfidfs[:n_important]}
    return important_words_to_spans(important_words, input)


@app.route('/tf-idf', methods=['POST'])
def handleTF_IDF():
    input = json.loads(request.data)
    words = input_to_words(input)
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

    sorted_tfidfs = sorted(results, key=operator.itemgetter('tf_idf'),
                           reverse=True)

    return json.dumps(sorted_tfidfs_to_spans(sorted_tfidfs, input))


def choose_n_important(sorted_pairs, min_share=0.05, max_share=0.4):
    if not sorted_pairs:
        return 0
    declines = [(prev[1] / cur[1], i)
                for i, (prev, cur)
                in enumerate(
                    zip(sorted_pairs, sorted_pairs[1:]),
                    start=1
                )]
    min_ind, max_ind = (int(share * len(sorted_pairs))
                        for share in [min_share, max_share])
    _, n_important = max(declines[min_ind : max_ind + 1])
    return n_important


@app.route('/w2v', methods=['POST'])
def highlight_with_v2w_norm():
    input = json.loads(request.data)
    words = input_to_words(input)

    no_normal = object()
    normalized_words = [morph.parse(word)[0].normal_form or no_normal
                        for word in words]
    
    norms = {normalized_word: vector_norms.get(normalized_word, 1e-6)
             for normalized_word in normalized_words}

    vector_norms_sorted = sorted(norms.items(),
                                 key=lambda x: x[1], 
                                 reverse=True)

    n_important = choose_n_important(vector_norms_sorted)

    important_normalized_words = {normalized_word for normalized_word, norm
                                  in vector_norms_sorted[:n_important]}
    important_words = {word for word, normalized_word
                       in zip(words, normalized_words)
                       if normalized_word in important_normalized_words}

    return json.dumps(important_words_to_spans(important_words, input))
