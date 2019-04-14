import json
import time
import string

from sumy_smr import sum_sents

import logging

script_start = time.time()
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.info('script starts now')


PUNCTUATION = string.punctuation + ''.join([
    '–', '—', '‒', '−', '«', '»', '\xa0', '°', '′', '\u2009', '\u200e',
    '©', '®', '’', '…', '↑', '″', '”', '“', '•', '№',
    ])


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


METHODS = {
    'lsa',
    'lexrank',
    'kl', # долго, остальные ок
    'luhn',
    'sumbasic',
    'textrank',
}

def handler(event, context):
    if event['httpMethod'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True,
                'Access-Control-Allow-Headers': 'Content-Type'
            }
        }
    func_start = time.time()
    logger.info('starting...')
    inp = json.loads(event["body"])['texts']

    texts = [x['text'] for x in inp]
    dlm = ' '
    joined = dlm.join(texts)

    sentences = sum_sents(joined, ratio=0.2, method='lsa')

    cur_start = 0
    spans = []
    for sent in sentences:
        beg = joined.find(sent, cur_start)
        if beg == -1:
            # print('====Not Found!!!====')
            # print(repr(sent))
            # print(repr(joined[cur_start : cur_start + 100]))
            continue
        cur_start = end = beg + len(sent)
        spans.append((beg, end))

    grouped_spans = joined_spans_to_grouped_spans(spans, texts, dlm, joined)

    logger.info('handling took %.3f' % (time.time() - func_start))
    logger.info(
        'time elapsed from script start: %.3f' % (time.time() - script_start)
    )
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type'
                    },
        'body': json.dumps(grouped_spans)
}
