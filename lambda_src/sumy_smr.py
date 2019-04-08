from math import ceil

from sumy.summarizers.lsa import LsaSummarizer
from sumy.summarizers.lex_rank import LexRankSummarizer
from sumy.summarizers.kl import KLSummarizer
from sumy.summarizers.luhn import LuhnSummarizer
from sumy.summarizers.sum_basic import SumBasicSummarizer
from sumy.summarizers.edmundson import EdmundsonSummarizer
from sumy.summarizers.text_rank import TextRankSummarizer

from nltk.stem.snowball import SnowballStemmer
from nltk.tokenize import word_tokenize, sent_tokenize


class Imposter():
    def __init__(self, text):
        self.text = text
        self._words = None
        self._sent = None

    @property
    def words(self):
        if self._words is None:
            self._words = word_tokenize(self.text)
        return self._words

    @property
    def sentences(self):
        if self._sent is None:
            self._sent = [Imposter(sent) for sent in sent_tokenize(self.text)]
        return self._sent

    def __repr__(self):
        return repr(self.text)


METHODS = {
    'lsa': LsaSummarizer,
    'lexrank': LexRankSummarizer,
    'kl': KLSummarizer,
    'luhn': LuhnSummarizer,
    'sumbasic': SumBasicSummarizer,
    'textrank': TextRankSummarizer,
}


def sum_sents(text, method, ratio=0.3, stemming=False):
    text_object = Imposter(text)
    if stemming:
        stemmer = SnowballStemmer('russian').stem
        summarizer = METHODS[method](stemmer)
    else:
        summarizer = METHODS[method]()
    sentences = [
        sent.text
        for sent in summarizer(text_object,
                               ceil(len(text_object.sentences) * ratio))]
    return sentences

