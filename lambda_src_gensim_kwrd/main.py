import json
import re

from gensim.summarization import keywords


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


def handler(event, context):
    inp = json.loads(event["body"])['texts']

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

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(grouped_spans)
    }
