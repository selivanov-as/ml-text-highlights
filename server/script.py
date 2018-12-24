from server.tf_idf_normalized import tf_idf_normalized
from server.samples_raw import samples_raw


def clean_words(words):
    cleaned_words = []

    for i, word in enumerate(words):
        if word[0] == "@":
            cleaned_words.append(word[1:])
        else:
            cleaned_words.append(word)
    return cleaned_words


def count_acc(words, results):
    wrong, right = 0, 0

    if len(words) != len(results):
        raise Exception("Result length isn't correct")

    for i, result in enumerate(results):
        highlightActual = words[i][0] == "@"
        highlightPredicted = result["highlight"]

        if highlightActual == highlightPredicted:
            right += 1
        else:
            wrong += 1

    return right / len(words)


print("Results for version with POS tagging:")
for sample in samples_raw:
    words = list(filter(lambda x: len(x) > 0, sample["words"]))
    words_cleaned = clean_words(words)

    results = tf_idf_normalized(words_cleaned)
    highlighted = list(filter(lambda x: x["highlight"], results))
    print("Highlight predictions:", list(map(lambda x: x["word"], highlighted)))
    print("Accuracy =", count_acc(words, results))

print("\nResults for version without POS tagging")
for sample in samples_raw:
    words = list(filter(lambda x: len(x) > 0, sample["words"]))
    words_cleaned = clean_words(words)

    results = tf_idf_normalized(words_cleaned, use_pos_tagging=False)
    highlighted = list(filter(lambda x: x["highlight"], results))
    print("Highlight predictions:", list(map(lambda x: x["word"], highlighted)))
    print("Accuracy =", count_acc(words, results))
