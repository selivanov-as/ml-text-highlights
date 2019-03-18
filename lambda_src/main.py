import itertools
import json
import string
from collections import Counter

import pymorphy2

morph = pymorphy2.MorphAnalyzer()

NORMS_FILE, LEMMR = ('./norms_sg_full.json', 'pymorphy')

PUNCTUATION = string.punctuation + ''.join([
    '–', '—', '‒', '−', '«', '»', '\xa0', '°', '′', '\u2009', '\u200e',
    '©', '®', '’', '…', '↑', '″', '”', '“', '•', '№',
])

with open('normalized_idf.json') as f:
    normalised_idf = json.loads(f.read())

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
    else:
        assert False, 'wrong lemmatiser, expected on of ["pymorphy"]'
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
    :param use_normalised: use set of normalised important words to determine
    spans (helps preventing mistakes due to unstable normalization)
    :param grouped_norm_words: normalized tokens grouped by node (must be
    provided if use_normalized == True)
    :param important_norm_words: set of important normalized words (must be
    provided if use_normalized == True)
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


def handler(event, context):
    inp = json.loads(event["body"])['texts']

    tokens, normalized_tokens = tokenize_lemmatize_input(inp, lem=LEMMR)

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

    spans = important_words_to_spans(
            important_tokens, inp, tokens,
            spaces_skipped=(LEMMR == 'pymorphy'),
            use_normalised=True, grouped_norm_words=normalized_tokens,
            important_norm_words=important_normalized_tokens)

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(spans)
    }
