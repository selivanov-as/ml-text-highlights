import string
import pymorphy2
import json
import itertools
import requests

morph = pymorphy2.MorphAnalyzer()
# from rus_preprocessing_mystem import (tag_mystem, mystem2upos)

NORMS_FILE, LEMMR = ('norms_ruscorpora_upos_cbow_300_20_2019.json', 'mystem')

PUNCTUATION = string.punctuation + ''.join([
    '–', '—', '‒', '−', '«', '»', '\xa0', '°', '′', '\u2009', '\u200e',
    '©', '®', '’', '…', '↑', '″', '”', '“', '•', '№',
])

with open(NORMS_FILE) as f:
    vector_norms = json.load(f)

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

    # elif lem == 'mystem':
    #     for text in texts:
    #         cur_tokens, cur_normalized_tokens = tag_mystem(
    #             text, mapping=mystem2upos
    #         )
    #         tokens.append(cur_tokens)
    #         normalized_tokens.append(cur_normalized_tokens)
    else:
        assert False, 'wrong lemmatiser, expected on of ["mystem", "pymorphy"]'
    return tokens, normalized_tokens


def important_words_to_spans(important_words, input,
                             grouped_words, spaces_skipped=True):
    """
    :param important_words: flat set of important (not normalized) words
    :param input: server input in unified format
    :param grouped_words: document tokens grouped by node (list of lists)
    :param spaces_skipped: if spaces skipped in tokenization
    :return: list of lists_of_spans_in_each_node;
    span is a tuple (begin_ind, end_ind) -- halfopen interval of a highlight
    """
    grouped_spans = []
    for node, words in zip(input, grouped_words):
        cur_pos = 0
        text = node['text']
        cur_spans = []
        for word in words:
            if word in important_words:
                beg = text.find(word, cur_pos)
                cur_pos = end = beg + len(word)
                cur_spans.append((beg, end))
            else:
                # trying to compensate for spaces - 1 per word in avg
                cur_pos += len(word) + int(spaces_skipped)
        grouped_spans.append(cur_spans)
    return grouped_spans

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

def handler(event, context):
    inp = json.loads(event["body"])

    tokens, normalized_tokens = tokenize_lemmatize_input(inp["texts"])

    norms = {normalized_token: vector_norms.get(normalized_token, float('-inf'))
             for normalized_token in itertools.chain(*normalized_tokens)}

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

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(important_words_to_spans(important_tokens, inp["texts"], tokens))
        # 'body': json.dumps(inp)
    }
