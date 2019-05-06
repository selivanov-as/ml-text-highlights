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


def input_to_words(input):
    texts = [x['text'] for x in input]
    return [word for word in
            (token.strip(PUNCTUATION)
             for text in texts
             for token in text.split())
            if word]  # should we strip?


def worddict_list_to_spans(worddicts, input):
    worddict_iterator = iter(worddicts)
    grouped_spans = []
    for node in input:
        cur_pos = 0
        text = node['text']
        cur_spans = []
        for word in text.split():
            worddict = {}
            try:
                while worddict.get('word') != word.strip(PUNCTUATION):
                    worddict = next(worddict_iterator)
            except StopIteration:
                print("can't find word", word)
                break
            if worddict.get('highlight'):
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
    results = tf_idf_normalized(words, use_pos_tagging=True)

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type'
                    },
        'body': json.dumps(worddict_list_to_spans(results, body["texts"]))
    }
