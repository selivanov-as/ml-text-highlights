import json
import random
import string

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
    important_words = sorted_tfidfs[:n_important]

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
    random.shuffle(words)

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type'
                    },
        'body': json.dumps(sorted_tfidfs_to_spans(words, body["texts"]))
    }
