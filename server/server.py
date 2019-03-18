import itertools
import json
import operator
import re
import string
import time
import threading
from collections import Counter
from pprint import pprint

# import pymorphy2
from flask import Flask, request
from gensim.summarization import keywords, summarize

# from entity_finder import find_entities
from sumy_smr import sum_sents


THR = 0.25
SHARE = 0.3
PUNCTUATION = string.punctuation + ''.join([
    '–', '—', '‒', '−', '«', '»', '\xa0', '°', '′', '\u2009', '\u200e',
    '©', '®', '’', '…', '↑', '″', '”', '“', '•', '№',
    ])

with open('../normalized_idf/normalized_idf.json') as f:
    normalised_idf = json.loads(f.read())

with open("./stopwords.txt") as f:
    stop_words_list = f.readlines()

stop_words = {}
for x in stop_words_list:
    stop_words[x.strip()] = True

# morph = pymorphy2.MorphAnalyzer()

app = Flask(__name__)


def joined_spans_to_grouped_spans(spans, texts, dlm, joined):
    borders = []
    end = -len(dlm)
    for text in texts:
        beg = end + len(dlm)
        end = beg + len(text)
        borders.append((beg, end))

    assert len(borders) == len(texts), (len(borders), len(texts))
    assert borders[-1][1] == len(joined), (borders[-1][1], len(joined))

    cur_ind = 0
    grouped_spans = []

    for (beg, end) in borders:
        start_ind = cur_ind
        while cur_ind < len(spans) and spans[cur_ind][1] < end:
            cur_ind += 1
        cur_spans = spans[start_ind : cur_ind]
        if cur_ind < len(spans) and spans[cur_ind][0] < end:
            # span is divided between text nodes
            cur_spans.append((spans[cur_ind][0], end))
        cur_spans = [tuple(max(0, x - beg) for x in span)
                            for span in cur_spans]
        grouped_spans.append(cur_spans)

    assert len(texts) == len(grouped_spans), (len(texts), len(grouped_spans))
    return grouped_spans
#
#
# def find_with_cfg_in_texts(texts, dlm=' '):
#     joined = dlm.join(texts)
#
#     #begin = time.perf_counter()
#     spans = find_entities(joined)
#     #cfg_time = time.perf_counter() - begin
#     #print(f'cfg_time: {cfg_time} s')
#
#     return joined_spans_to_grouped_spans(spans, texts, dlm, joined)
#
#
# @app.route('/cfg', methods = ['POST'])
# def work_with_cfg():
#     #begin = time.perf_counter()
#     input = json.loads(request.data)
#     texts = [x['text'] for x in input]
#     spans = find_with_cfg_in_texts(texts)
#     #overall_time = time.perf_counter() - begin
#     #print(f'overall time: {overall_time} s')
#     return json.dumps(spans)
#
#
# def input_to_words(input):
#     texts = [x['text'] for x in input]
#     return [word for word in
#                 (token.strip(PUNCTUATION)
#                  for text in texts
#                  for token in text.split())
#                 if word]  # shoul we strip?
#
#
# def sorted_tfidfs_to_spans(sorted_tfidfs, input):
#     n_important = int(len(sorted_tfidfs) * SHARE)
#     important_words = {tf_idf_info['word'] for tf_idf_info in sorted_tfidfs[:n_important]}
#
#     grouped_spans = []
#     for node in input:
#         cur_pos = 0
#         text = node['text']
#         cur_spans = []
#         for word in text.split():
#             if word.strip(PUNCTUATION) in important_words:
#                 beg = text.find(word, cur_pos)
#                 cur_pos = end = beg + len(word)
#                 cur_spans.append((beg, end))
#             else:
#                 cur_pos += len(word) + 1
#         grouped_spans.append(cur_spans)
#     return grouped_spans
#
#
# @app.route('/tf-idf', methods=['POST'])
# def handleTF_IDF():
#     input = json.loads(request.data)
#     words = input_to_words(input)
#     normalized_words = []
#     results = []
#     included_normal_forms = {}
#
#     for i, word in enumerate(words):
#         normalized_words.append(morph.parse(word)[0].normal_form)
#
#     doc_length = len(normalized_words)
#     for i, word in enumerate(normalized_words):
#         if (word.isnumeric()): continue
#
#         word_normal_form = morph.parse(word)[0].normal_form
#         word_normal_form_idf = normalised_idf.get(word_normal_form)
#
#         word_normal_form_exist = word_normal_form_idf is not None
#         word_is_not_in_stop_words_list = stop_words.get(words[i]) is None and stop_words.get(word_normal_form) is None
#
#         if word_normal_form_exist and word_is_not_in_stop_words_list:
#             tf_idf_info = {
#                 'word': words[i],
#                 'tf_idf': normalized_words.count(word) / doc_length * 1000 / word_normal_form_idf,
#                 'tf': normalized_words.count(word),
#                 'doc_length': doc_length,
#                 'idf': word_normal_form_idf
#             }
#
#         elif not word_normal_form_exist:
#             tf_idf_info = {
#                 'word': words[i],
#                 'tf_idf': 1337,
#                 'tf': normalized_words.count(word),
#                 'doc_length': doc_length,
#                 'idf': word_normal_form_idf
#             }
#
#         if included_normal_forms.get(word_normal_form) is None:
#             results.append(tf_idf_info)
#             included_normal_forms[word_normal_form] = True
#
#     sorted_tfidfs = sorted(results, key=operator.itemgetter('tf_idf'), reverse=True)
#
#     return json.dumps(sorted_tfidfs_to_spans(sorted_tfidfs, input))


@app.route('/gensim_kwrd', methods=['POST'])
def gensim_kwrd():
    inp = json.loads(request.data)['texts']
    texts = [x['text'] for x in inp]

    dlm = ' '
    joined = dlm.join(texts).lower()

    kwrds = keywords(joined, ratio=0.3, scores=False, split=True)

    # if one of the keywords is a prefix of another one,
    # it should be searched for after its superstring keyword:
    kwrds.sort(reverse=True)
    regexp_parts = []
    for kwrd in kwrds:
        splitted = kwrd.split()  # for single-word kwrd - 1 el list
        regexp_parts.append(r'\b' + r'\b\W+\b'.join(splitted) + r'\b')
    regexp = re.compile(r'|'.join(regexp_parts))
    spans = [match.span() for match in re.finditer(regexp, joined)]

    grouped_spans = joined_spans_to_grouped_spans(spans, texts, dlm, joined)
    return json.dumps(grouped_spans)


@app.route('/gensim_sentences', methods=['POST'])
def gensim_sentences():
    inp = json.loads(request.data)['texts']

    texts = [x['text'] for x in inp]
    dlm = ''
    joined = dlm.join(texts)

    sentences = summarize(joined, ratio=0.2, split=True)

    cur_start = 0
    spans = []
    for sent in sentences:
        beg = joined.find(sent, cur_start)
        if beg == -1:
            print('====Not Found!!!====')
            print(repr(sent))
            print(repr(joined[cur_start : cur_start + 100]))
            continue
        cur_start = end = beg + len(sent)
        spans.append((beg, end))

    grouped_spans = joined_spans_to_grouped_spans(spans, texts, dlm, joined)
    return json.dumps(grouped_spans)


METHODS = {
    'lsa',
    'lexrank',
    'kl', # долго, остальные ок
    'luhn',
    'sumbasic',
    'textrank',
}



@app.route('/sumy', methods=['POST'])
def sumy_summarize():
    inp = json.loads(request.data)['texts']

    texts = [x['text'] for x in inp]
    dlm = ''
    joined = dlm.join(texts)

    sentences = sum_sents(joined, ratio=0.2, method='luhn')

    cur_start = 0
    spans = []
    for sent in sentences:
        beg = joined.find(sent, cur_start)
        if beg == -1:
            print('====Not Found!!!====')
            print(repr(sent))
            print(repr(joined[cur_start : cur_start + 100]))
            continue
        cur_start = end = beg + len(sent)
        spans.append((beg, end))

    grouped_spans = joined_spans_to_grouped_spans(spans, texts, dlm, joined)
    return json.dumps(grouped_spans)

