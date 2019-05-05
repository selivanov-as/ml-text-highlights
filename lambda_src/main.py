import json
import string
import pymorphy2
import operator
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

from tf_idf_normalized import tf_idf_normalized

morph = pymorphy2.MorphAnalyzer()

PUNCTUATION = string.punctuation + "–—‒"

SHARE = 0.3


def input_to_words(input):
    texts = [x['text'] for x in input]
    return [word for word in
            (token.strip(PUNCTUATION)
             for text in texts
             for token in text.split())
            if word]  # should we strip?


def sorted_tfidfs_to_spans(sorted_tfidfs, input):
    n_important = int(len(sorted_tfidfs) * SHARE)
    important_words = {tf_idf_info['word'] for tf_idf_info in \
                       list(filter(lambda word: 'highlight' in word and word['highlight'] == True, sorted_tfidfs))}

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

    body = json.loads(event["body"])
    words = input_to_words(body["texts"])
    results = tf_idf_normalized(words, use_pos_tagging=False)
    sorted_tfidfs = sorted(results, key=lambda word: word['tf_idf'], reverse=True)

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type'
                    },
        'body': json.dumps(sorted_tfidfs_to_spans(sorted_tfidfs, body["texts"]))
    }
