import pymorphy2
import codecs
import time
import json
from collections import Counter
import operator

morph = pymorphy2.MorphAnalyzer()
pos_dict, pos_set = dict(), set()
used_normal_forms_in_current_article = dict()
IS_DEBUG = True


def process_article_with_pos_tagger(article):
    pos_dict.clear()
    pos_dict["tokens_amount"] = 0

    for w in article.strip().split(" "):
        parse_result = morph.parse(w)[0]
        normal_form, pos = parse_result.normal_form, parse_result.tag.POS
        should_use_normal_form = pos == "NOUN" or pos == "ADJF" or pos == "ADJS" or pos == "VERB" or pos == "INFN"
        token_to_append = normal_form if should_use_normal_form else w

        if pos in pos_dict:
            pos_dict[pos].append(token_to_append)
        else:
            pos_dict[pos] = [token_to_append]

        pos_dict["tokens_amount"] += 1
        pos_set.add(pos)


file_name = "wiki.ru.text"

with codecs.open(file_name, "r", "utf-8") as fin:
    start_time, articles_amount = time.time(), 0

    for i, line in enumerate(fin):  # traverses each article
        process_article_with_pos_tagger(line)
        articles_amount += 1

        if i > 0 and i % 13233 == 0:
            print(f"Processed {i} articles.")
            print(f"{(time.time() - start_time) // 60} minutes elapsed for last 5000 articles")
            print()

            start_time = time.time()

        if IS_DEBUG:
            if i >= 500:
                break

    print(f"{articles_amount // 1265739 * 100} articles processed. Saving pos dictionary...")

    for pos in pos_set:
        words_of_particular_pos = Counter(pos_dict[pos])
        words_of_particular_pos_sorted = sorted(words_of_particular_pos.items(), reverse=True,
                                                key=operator.itemgetter(1))
        pos_dict[pos] = words_of_particular_pos_sorted[0:100]

    with open("pymorphy2.json", "w", encoding="utf-8") as fp:
        json.dump(pos_dict, fp, ensure_ascii=False)
