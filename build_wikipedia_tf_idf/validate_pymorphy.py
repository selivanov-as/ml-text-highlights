import pymorphy2
import codecs
import time
import itertools
import json
from collections import Counter
import operator
import pickle

morph = pymorphy2.MorphAnalyzer()

IS_DEBUG = False


def process_article_with_pos_tagger(article):

    raw_tokens = article.strip().split()
    try:
        processed = [morph.parse(token)[0] for token in raw_tokens]
    except (KeyError, ValueError):
        return Counter()
    processed = [(parsed.normal_form, str(parsed.tag.POS), raw_token)  # yep, lets store original tokens too, just in case
                 for parsed, raw_token in zip(processed, raw_tokens)]

    return Counter(processed)

# отличается предобработкой с удалением ударений, разбивающих слова
file_name = "../wiki.ru.wo_emph.text"   #  "wiki.ru.text"

with open(file_name, encoding="utf-8") as fin:
    counts = Counter()

    start = prev = time.perf_counter()
    n = 1000
    for i, line in enumerate(fin):  # traverses each article
        cur_counts = process_article_with_pos_tagger(line)
        # counts += cur_counts  # suprisingly, this is O(len(counts))
        for k, v in cur_counts.items():
            counts[k] += v

        if i and i % n == 0:
            cur = time.perf_counter()
            total = int(cur - start)
            print(f'{i}it',
                  f'{total // (60*60)}:{total % (60*60) // 60}:{total % 60}',
                  f'{round(n / (cur - prev), 2)}it/s')
            prev = cur

        if IS_DEBUG:
            if i >= 5 * n:
                break

print(f"{i + 1} articles processed. Saving pos dictionary...")

# save raw counts
with open('raw_counts.pkl', 'wb') as f:
    pickle.dump(counts, f)

tokens_amount = sum(counts.values())
sorted_by_tag = sorted(counts.items(), key=lambda t: t[0][1])

by_tag = {}
# itertools magic
for tag, tokens_with_same_tag in itertools.groupby(sorted_by_tag,
                                                   key=lambda t: t[0][1]):
    by_tag[tag] = list(tokens_with_same_tag)

for tag in by_tag:
    tokens_with_same_tag = by_tag[tag]
    sorted_by_nf = sorted(tokens_with_same_tag, key=lambda t: t[0][0])
    grouped_by_nf = [(normal_form, sum(t[1] for t in same_nf))
                     for normal_form, same_nf in itertools.groupby(
                         sorted_by_nf, key=lambda t: t[0][0]
                     )]
    grouped_by_nf.sort(key=lambda pair: pair[1], reverse=True)
    by_tag[tag] = grouped_by_nf

by_tag['tokens_amount'] = tokens_amount
with open("pymorphy2_.json", "w", encoding="utf-8") as fp:
    json.dump(by_tag, fp, ensure_ascii=False)
