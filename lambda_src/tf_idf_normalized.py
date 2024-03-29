import pymorphy2
import json
from nltk import RegexpParser
from percentile import percentile

with open('./normalized_idf.json') as f:
    normalised_idf = json.loads(f.read())

with open("./stopwords.txt") as f:
    stop_words_list = f.readlines()

stop_words = {}
for x in stop_words_list:
    stop_words[x.strip()] = True

morph = pymorphy2.MorphAnalyzer()


def tf_idf_normalized(words, use_pos_tagging=True):
    normalized_words = []
    result = []
    included_tf_idf_values = []

    for i, word in enumerate(words):
        normalized_words.append(morph.parse(word)[0].normal_form)

    # Calculate if-idf values
    create_tf_idf_info(result, words, normalized_words, included_tf_idf_values)

    # Calculate highlight threshold (get first 30% of list)
    included_tf_idf_values_sorted = sorted(included_tf_idf_values, reverse=True)
    highlight_threshold = percentile(included_tf_idf_values_sorted, percent=0.7)

    for word in result:
        if word["tf_idf"] >= highlight_threshold:
            word["highlight"] = True
        else:
            word["highlight"] = False

    if use_pos_tagging:
        pos_tagging(list(filter(lambda word: word.get("normal_form") is not None, result)))

    return result


def create_tf_idf_info(result, words, normalized_words, included_tf_idf_values):
    included_normal_forms = {}

    doc_length = len(normalized_words)
    for i, word_in_normal_form in enumerate(normalized_words):
        if (word_in_normal_form.isnumeric()):
            tf_idf_info = {
                'word': words[i],
                'tf_idf': 0,
                'normal_form': word_in_normal_form,
                'tf': normalized_words.count(word_in_normal_form),
                'doc_length': doc_length,
                'idf': word_normal_form_idf
            }
            result.append(tf_idf_info)

            continue

        word_normal_form_idf = normalised_idf.get(word_in_normal_form)

        word_normal_form_idf_exist = word_normal_form_idf is not None
        word_is_not_in_stop_words_list = stop_words.get(word_in_normal_form) is None and stop_words.get(
            word_in_normal_form) is None

        if not word_is_not_in_stop_words_list:
            tf_idf_info = {
                'word': words[i],
                'tf_idf': 0,
                'normal_form': word_in_normal_form,
                'tf': normalized_words.count(word_in_normal_form),
                'doc_length': doc_length,
                'idf': word_normal_form_idf
            }

        elif word_normal_form_idf_exist and word_is_not_in_stop_words_list:
            tf_idf_info = {
                'word': words[i],
                'normal_form': word_in_normal_form,
                'tf_idf': normalized_words.count(word_in_normal_form) / doc_length * 1000 / word_normal_form_idf,
                'tf': normalized_words.count(word_in_normal_form),
                'doc_length': doc_length,
                'idf': word_normal_form_idf
            }

        elif not word_normal_form_idf_exist:
            tf_idf_info = {
                'word': words[i],
                'tf_idf': 0,
                'normal_form': word_in_normal_form,
                'tf': normalized_words.count(word_in_normal_form),
                'doc_length': doc_length,
                'idf': word_normal_form_idf
            }

        # if included_normal_forms.get(word_in_normal_form) is None:
        result.append(tf_idf_info)
        included_tf_idf_values.append(tf_idf_info['tf_idf'])
        # included_normal_forms[word_in_normal_form] = True


def pos_tagging(result):
    pos_tagged_words = []
    for tf_idf_info in result:
        tf_idf_info["pos"] = morph.parse(tf_idf_info["normal_form"])[0].tag.POS
        if tf_idf_info["pos"] is not None:
            pos_tagged_words.append((tf_idf_info["normal_form"], tf_idf_info["pos"]))

    # ToDo: Add reg exps for numeric
    patterns = """
                    many adj+noun:{<ADJF>+<NOUN>}
                    noun+many adj:{<NOUN><ADJF>+}
                    verb + noun:{<INFN><NOUN>+}
                    verb + verb:{<INFN><INFN>}
                    prep + verb/noun:{<PRCL>(<INFN>|<NOUN>)} 
                    verb + prep + verb?:{<INFN><PRCL><INFN>?}
                    conj + verb/verb + conj:{(<INFN><CONJ>)|(<CONJ><INFN>)?}
               """

    chunker = RegexpParser(patterns)
    tree = chunker.parse(pos_tagged_words)

    for subtree in tree.subtrees():
        if subtree._label == "S":
            continue

        # highlight all words in collocation if one of them already was highlighted
        # TODO: Iterate through all elements of subtree (it might be > 2)
        term1, term2 = subtree[0][0], subtree[1][0]
        tf_idf_info1, tf_idf_info2 = next(x for x in result if x["normal_form"] == term1), \
                                     next(x for x in result if x["normal_form"] == term2)

        if tf_idf_info1["highlight"] or tf_idf_info2["highlight"]:
            tf_idf_info1["highlight"], tf_idf_info2["highlight"] = True, True
