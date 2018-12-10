import json
import random
import string
from glob import iglob as list_paths


def find_word_borders(text):
    borders = []
    words = text.split()
    start = 0
    for word in words:
        word_beg = text.find(word, start)
        start = word_end = word_beg + len(word)
        borders.append((word_beg, word_end))
    return borders


def inds_to_spans(text, inds):
    inds.sort()
    spans = []
    borders = find_word_borders(text)
    for ind in inds:
        spans.append(borders[ind])
    return spans


def spans_to_inds(text, spans):
    spans.sort()
    inds = []
    borders = find_word_borders(text)
    cur_ind = 0
    for span in spans:
        while cur_ind < len(borders) and borders[cur_ind][1] <= span[0]:
            cur_ind += 1
        while cur_ind < len(borders) and borders[cur_ind][0] < span[1]:
            inds.append(cur_ind)
            cur_ind += 1
    return inds


def test(max_word=15, max_dict=20_000, max_text=100, highlight_share=0.1, n_iter=10_000):
    words = {''.join(random.choices(string.ascii_lowercase, k=random.randrange(1, max_word))) for _ in range(max_dict)}
    #print(len(words))
    for _ in range(n_iter):
        text_len = random.randrange(1, max_text)
        word_seq = random.choices(list(words), k=text_len)
        text = ' '.join(word_seq)
        inds = random.sample(range(text_len), k=int(highlight_share * text_len))
        assert inds == spans_to_inds(text, inds_to_spans(text, inds)), (inds, spans_to_inds(text, inds_to_spans(text, inds)))
    print('test ok')


def precision(inds_true, inds_pred):
    if not inds_pred:
        return None
    return len(set(inds_true) & set(inds_pred)) / len(set(inds_pred))


def recall(inds_true, inds_pred):
    if not inds_true:
        return None
    return len(set(inds_true) & set(inds_pred)) / len(set(inds_true))


def f1(inds_true, inds_pred):
    pr, rec = precision(inds_true, inds_pred), recall(inds_true, inds_pred)
    if pr is None or rec is None:
        return None
    if pr + rec == 0:
        return 0
    return 2 * pr * rec / (pr + rec)


def load_text(path):
    with open(path, encoding='utf-8') as file:
        return file.read()


def load_inds(path):
    with open(path) as f:
        inds = json.loads(f.read())
    return inds


def human_friendly_print(path_exp=None, line_len=5, word_width=20):
    if path_exp is None:
        path_exp = input('path to text files:')
    for path in list_paths(path_exp):
        print()
        print(path)
        text = load_text(path)
        words = text.split()
        t = []
        print()
        for i, word in enumerate(words):
            t.append((i, word))
            if len(t) == line_len or i == len(words) - 1:
                print(''.join([x[1].ljust(word_width) for x in t]))
                print(''.join([str(x[0]).ljust(word_width) for x in t]))
                print()
                t = []