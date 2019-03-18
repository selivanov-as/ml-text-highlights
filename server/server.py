import itertools
import json
import operator
import re
import string
import time
import threading
from collections import Counter
from pprint import pprint

import pymorphy2
from flask import Flask, request

# import matplotlib.pyplot as plt
# from entity_finder import find_entities
# from rus_preprocessing_mystem import (tag_mystem, mystem2upos)


THR = 0.25
SHARE = 0.3
PUNCTUATION = string.punctuation + ''.join([
    '–', '—', '‒', '−', '«', '»', '\xa0', '°', '′', '\u2009', '\u200e',
    '©', '®', '’', '…', '↑', '″', '”', '“', '•', '№',
    ])
# NORMS_FILE, LEMMR = ('./norms_sg_base.json', 'pymorphy')
# NORMS_FILE, LEMMR = ('./norms_cbow_base.json', 'pymorphy')
# NORMS_FILE, LEMMR = ('./norms_glove_50k.json', 'pymorphy')
NORMS_FILE, LEMMR = ('./norms_sg_full.json', 'pymorphy')
# NORMS_FILE, LEMMR = ('./norms_cbow_full.json', 'pymorphy')
# NORMS_FILE, LEMMR = (
#     'norms_ruwikiruscorpora-func_upos_skipgram_300_5_2019.json', 'mystem')
# NORMS_FILE, LEMMR = (
#     'norms_ruwikiruscorpora_upos_skipgram_300_2_2019.json', 'mystem')
# NORMS_FILE, LEMMR = ('norms_ruscorpora_upos_cbow_300_20_2019.json', 'mystem')
# NORMS_FILE, LEMMR = ('norms_tenth.norm-sz500-w7-cb0-it5-min5.json', None)


with open('../normalized_idf/normalized_idf.json') as f:
    normalised_idf = json.loads(f.read())

with open("./stopwords.txt") as f:
    stop_words_list = f.readlines()

with open(NORMS_FILE) as f:
    vector_norms = json.load(f)


def median(somelist):
    if not somelist:
        return None
    if len(somelist) % 2:  # odd num of el
        return somelist[len(somelist) // 2]
    else:
        return (somelist[len(somelist) // 2]
                + somelist[len(somelist) // 2 + 1]) / 2


median_idf = median(sorted(normalised_idf.values()))
median_norm = median(sorted(vector_norms.values()))

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


def tokenize_lemmatize_input(inp, lem='pymorphy'):
    """
    :param inp: server input in unified format
    :param lem: tokeniztaion and lemmatisation method
    :return: grouped tokens and grouped lemmatised tokens,
    grouping is by node, same as in inp
    """
    texts = (x['text'] for x in inp)
    tokens, normalized_tokens = [], []
    if lem == 'pymorphy':
        no_normal = object()
        for text in texts:
            cur_tokens = [word for word in
                          (token.strip(PUNCTUATION)
                           for token in text.split())
                          if word]
            cur_normalized_tokens = [
                morph.parse(word)[0].normal_form or no_normal
                for word in cur_tokens]
            tokens.append(cur_tokens)
            normalized_tokens.append(cur_normalized_tokens)
    elif lem == 'mystem':
        for text in texts:
            cur_tokens, cur_normalized_tokens = tag_mystem(
                text, mapping=mystem2upos
            )
            tokens.append(cur_tokens)
            normalized_tokens.append(cur_normalized_tokens)
    elif lem is None:
        tokens = [text.split() for text in texts]
        normalized_tokens = list(tokens)
    else:
        assert False, '''wrong lemmatiser, expected on of ["mystem", "pymorphy", None]'''
    return tokens, normalized_tokens


def important_words_to_spans(important_words, input,
                             grouped_words, spaces_skipped=True,
                             use_normalised=False, grouped_norm_words=None,
                             important_norm_words=None):
    """
    :param important_words: flat set of important (not normalized) words
    :param input: server input in unified format
    :param grouped_words: document tokens grouped by node (list of lists)
    :param spaces_skipped: if spaces skipped in tokenization
    :return: list of lists_of_spans_in_each_node;
    span is a tuple (begin_ind, end_ind) -- halfopen interval of a highlight
    """
    grouped_spans = []
    for i, (node, words) in enumerate(zip(input, grouped_words)):
        cur_pos = 0
        text = node['text']
        cur_spans = []
        for j, word in enumerate(words):
            if (
                    (use_normalised
                     and grouped_norm_words[i][j] in important_norm_words)
                    or (not use_normalised and word in important_words)
            ):
                beg = text.find(word, cur_pos)
                cur_pos = end = beg + len(word)
                cur_spans.append((beg, end))
            else:
                # trying to compensate for spaces - 1 per word in avg
                cur_pos += len(word) + int(spaces_skipped)
        grouped_spans.append(cur_spans)
    return grouped_spans


def sorted_tfidfs_to_spans(sorted_tfidfs, input, grouped_words):
    n_important = int(len(sorted_tfidfs) * SHARE)
    important_words = {tf_idf_info['word']
                       for tf_idf_info in sorted_tfidfs[:n_important]}
    return important_words_to_spans(important_words, input, grouped_words)


def choose_n_important(sorted_pairs, min_share=0.05, max_share=0.4):
    if not sorted_pairs:
        return 0
    declines = [(prev[1][0] / cur[1][0], i)
                for i, (prev, cur)
                in enumerate(
                    zip(sorted_pairs, sorted_pairs[1:]),
                    start=1
                )]
    min_ind, max_ind = (int(share * len(sorted_pairs))
                        for share in [min_share, max_share])
    _, n_important = max(declines[min_ind : max_ind + 1])
    return n_important


@app.route('/tf-idf', methods=['POST'])
def handleTF_IDF():
    input = json.loads(request.data)
    gr_words, gr_normalized_words = tokenize_lemmatize_input(
        input, lem='pymorphy'
    )
    words = list(itertools.chain(*gr_words))
    normalized_words = list(itertools.chain(*gr_normalized_words))

    results = []
    included_normal_forms = {}

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

    return json.dumps(sorted_tfidfs_to_spans(sorted_tfidfs, input, gr_words))


DEBUG_PRINT = False
USE_TFIDF_W2V_PRODUCT = True


@app.route('/w2v', methods=['POST'])
def highlight_with_w2v_norm():
    inp = json.loads(request.data)['texts']

    tokens, normalized_tokens = tokenize_lemmatize_input(inp, lem=LEMMR)

    if not USE_TFIDF_W2V_PRODUCT:
        if LEMMR is None:
            norms = {}
            for normalized_token in itertools.chain(*normalized_tokens):
                stripped = normalized_token.strip(
                    PUNCTUATION + string.whitespace
                )
                norm = (
                    vector_norms.get(normalized_token)
                    or vector_norms.get(stripped)
                    or vector_norms.get(morph.parse(stripped)[0].normal_form)
                    or float('-inf')
                )
                norms[normalized_token] = (norm,)
        else:
            norms = {normalized_token: (vector_norms.get(normalized_token, float('-inf')),)
                     for normalized_token in itertools.chain(*normalized_tokens)}
    else:
        norms = {}
        tfs = Counter(itertools.chain(*normalized_tokens))
        doc_length = sum(1 for _ in itertools.chain(*normalized_tokens))
        for normalized_token in itertools.chain(*normalized_tokens):
            lemma = normalized_token.split('_')[0]
            if (not lemma  # normal form doesn't exist
                or all(c in (PUNCTUATION + string.whitespace + string.digits)
                       for c in lemma)):  # normal form doesn't have letters
                norms[normalized_token] = (float('-inf'),)
            else:
                idf = 1 / normalised_idf.get(lemma, median_idf)
                tf = tfs[normalized_token]
                vnorm = vector_norms.get(normalized_token, median_norm)
                norms[normalized_token] = (
                    tf * idf * vnorm**(16) * 1_000_000 / doc_length,
                    tf * idf * 1_000_000 / doc_length, tf, 1/idf, vnorm
                )

    vector_norms_sorted = sorted(norms.items(),
                                 key=lambda x: x[1],
                                 reverse=True)

    n_important = choose_n_important(vector_norms_sorted,
                                     min_share=0.2, max_share=0.3)

    important_normalized_tokens = {normalized_word for normalized_word, norm
                                   in vector_norms_sorted[:n_important]}

    important_tokens = {token
                        for cur_tokens, cur_normalized_tokens
                        in zip(tokens, normalized_tokens)
                        for token, normalized_token
                        in zip(cur_tokens, cur_normalized_tokens)
                        if normalized_token in important_normalized_tokens}

    if not DEBUG_PRINT:
        return json.dumps(
            important_words_to_spans(
                important_tokens, inp, tokens,
                spaces_skipped=(LEMMR == 'pymorphy'),
                use_normalised=True, grouped_norm_words=normalized_tokens,
                important_norm_words=important_normalized_tokens)
        )

    grouped_words = tokens
    input = inp
    important_words = important_tokens
    spaces_skipped = (LEMMR == 'pymorphy')
    use_normalised = True
    grouped_norm_words = normalized_tokens
    important_norm_words = important_normalized_tokens
    #
    min_norm = vector_norms_sorted[n_important - 1][1]
    hl_share = n_important / len(vector_norms_sorted)
    # with open(f'{NORMS_FILE.split(".")[0]}_plot_info.json', 'w') as f:
    #     json.dump({
    #         'sorted_norms': vector_norms_sorted,
    #         'min_norm': min_norm
    #     }, f)
    print(30 * '\n',
          f'min_highlighted_norm = {min_norm}',
          f'highlighted_share = {round(hl_share, 2)}',
          f'median_idf = {median_idf}',
          f'median_norm = {median_norm}',
          '_____________________________________________',
          sep='\n')
    debug_printing = False
    ### example-specific
    start_promoters = ['Туркиль из Беркшира', 'поликистозом',
                       'дав начало созданию государственного аппарата Литвы']
    end_promoters = ['армия Гарольда достигла Гастингса',
                     'Соматические нарушения, сопутствующие делирию',
                     'В 1921 году страна была принята в']
    delim = ' ' if LEMMR == 'pymorphy' else ''
    #
    grouped_spans = []
    for i, (node, words) in enumerate(zip(input, grouped_words)):
        cur_pos = 0
        text = node['text']
        cur_spans = []
        #
        debug_text = []
        punkt_space = PUNCTUATION + string.whitespace
        #
        for j, word in enumerate(words):
            if (
                    (use_normalised
                     and grouped_norm_words[i][j] in important_norm_words)
                    or (not use_normalised and word in important_words)
            ):
                beg = text.find(word, cur_pos)
                cur_pos = end = beg + len(word)
                cur_spans.append((beg, end))
                #
                highlighted = True
                #
            else:
                # trying to compensate for spaces - 1 per word in avg
                cur_pos += len(word) + int(spaces_skipped)
                #
                highlighted = False
                #
            #
            mark = '*' if highlighted else ''
            no_norm = all(c in punkt_space for c in word)
            info = ";".join(
                [format(el, ".1f") for el in norms.get(
                    grouped_norm_words[i][j], (float("-inf"),)
                )]
            )
            norm = (f'|{info}|' if not no_norm else '')
            debug_text.append(f'{mark}{word}{mark}{norm}')
            #
        #
        if debug_printing:
            print(delim.join(debug_text), end='')
        if any(p in text for p in start_promoters):
            debug_printing = True
        elif any(p in text for p in end_promoters):
            debug_printing = False
            print()
        #
        grouped_spans.append(cur_spans)
    return json.dumps(grouped_spans)
