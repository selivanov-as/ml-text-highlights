import sys
from natasha import (
    NamesExtractor,
    #PersonExtractor,
    #LocationExtractor,
    AddressExtractor,
    #OrganisationExtractor,
    DatesExtractor,
    #MoneyExtractor,
    #MoneyRateExtractor,
    #MoneyRangeExtractor,
)


def unite_spans(spans):
    '''makes list of disjoint spans'''
    if not spans:
        return spans
    spans = sorted(spans, key=lambda x: (x.start, x.stop))
    new_spans = []
    beg, end = spans[0].start, spans[0].stop
#     prev = spans[0]
    for span in spans[1:]:
        if span.start < end < span.stop:
            end = span.stop
        elif span.stop <= end:
            continue
        else:
            new_spans.append((beg, end))
            beg, end = span.start, span.stop
    new_spans.append((beg, end))
    return new_spans


def find_entities(text):
    all_spans = []
    for extr_cls in (
        NamesExtractor,
        #PersonExtractor,
        #LocationExtractor,
        AddressExtractor,
        #OrganisationExtractor,
        DatesExtractor,
        #MoneyExtractor,
        #MoneyRateExtractor,
        #MoneyRangeExtractor,
    ):
        extractor = extr_cls()
        matches = extractor(text)
        spans = [_.span for _ in matches]
        all_spans.extend(spans)
    return unite_spans(all_spans)


if __name__ == '__main__':
    text = sys.stdin.read()
    print(find_entities(text))