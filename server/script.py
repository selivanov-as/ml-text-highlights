from tf_idf_normalized import tf_idf_normalized
from samples_raw import samples_raw

METHOD = tf_idf_normalized


def clean_words(words):
    cleaned_words = []

    for i, word in enumerate(words):
        if word[0] == "@":
            cleaned_words.append(word[1:])
        else:
            cleaned_words.append(word)
    return cleaned_words


def count_acc(words, results):
    right = 0

    if len(words) != len(results):
        raise Exception("Result length isn't correct")

    for i, result in enumerate(results):
        highlightActual = words[i][0] == "@"
        highlightPredicted = result["highlight"]

        if highlightActual == highlightPredicted:
            right += 1

    return right / len(words)


def count_precision(words, results):
    tp, tn, fp, fn = 0, 0, 0, 0

    if len(words) != len(results):
        raise Exception("Result length isn't correct")

    for i, result in enumerate(results):
        highlightActual = words[i][0] == "@"
        highlightPredicted = result["highlight"]

        if highlightActual == highlightPredicted:
            tp += 1
        if highlightActual == False and highlightPredicted == True:
            fp += 1

    return tp / (tp + fp)


def count_recall(words, results):
    tp, tn, fn = 0, 0, 0

    if len(words) != len(results):
        raise Exception("Result length isn't correct")

    for i, result in enumerate(results):
        highlightActual = words[i][0] == "@"
        highlightPredicted = result["highlight"]

        if highlightActual == highlightPredicted:
            tp += 1
        if highlightActual == True and highlightPredicted == False:
            fn += 1

    return tp / (tp + fn)


print("Results for version with POS tagging:")
for sample in samples_raw:
    words = list(filter(lambda x: len(x) > 0, sample["words"]))
    words_cleaned = clean_words(words)

    results = METHOD(words_cleaned)
    highlighted = list(filter(lambda x: x["highlight"], results))
    print(f"Highlight predictions: {list(map(lambda x: x['word'], highlighted))}")
    print(f"Accuracy = {count_acc(words, results)}")
    precision = count_precision(words, results)
    recall = count_recall(words, results)
    print(f"Precision = {precision}")
    print(f"Recall = {recall}")
    print(f"F-score = {2 * precision * recall / (precision + recall)}")

    # print("\nResults for version without POS tagging")
    # for sample in samples_raw:
    #     words = list(filter(lambda x: len(x) > 0, sample["words"]))
    #     words_cleaned = clean_words(words)
    #
    #     results = METHOD(words_cleaned, use_pos_tagging=False)
    #     highlighted = list(filter(lambda x: x["highlight"], results))
    #     print(f"Highlight predictions: {list(map(lambda x: x['word'], highlighted))}")
    #     print(f"Accuracy = {count_acc(words, results)}")
    #     precision = count_precision(words, results)
    #     recall = count_recall(words, results)
    #     print(f"Precision = {precision}")
    #     print(f"Recall = {recall}")
    #     print(f"F-score = {2 * precision * recall / (precision + recall)}")
