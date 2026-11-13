from labeler.keyword_matcher import match_keywords, parse_keywords
from labeler.labeling_engine import run_keyword_query
from labeler.models import Note


def test_parse_keywords_splits_trims_and_drops_duplicates():
    assert parse_keywords(" car,Truck,, CAR ;hit   by\nbus, respect*, * ") == ["car", "Truck", "hit by", "bus", "respect*"]


def _labels(texts, keywords):
    return [r.label for r in match_keywords(texts, keywords)]


def test_whole_words_case_ignored():
    assert _labels(["My CAR", "my car,", "car.", "a scar", "the carpet"], ["car"]) == [1, 1, 1, 0, 0]


def test_punctuation_and_apostrophes():
    assert _labels(["the car's door", "the car’s door", "car-free street", "(car)"], ["car"]) == [1, 1, 1, 1]


def test_wildcard_matches_word_starts():
    texts = ["respect", "respects", "they respected it", "respecting rules", "disrespect", "respite"]
    assert _labels(texts, ["respect*"]) == [1, 1, 1, 1, 0, 0]


def test_special_characters_match_literally():
    assert _labels(["I write c++ daily", "a.b here", "axb", "(x) marks", "x alone"], ["c++", "a.b", "(x)"]) == [1, 1, 0, 1, 0]


def test_any_of_several_words_and_phrases():
    assert _labels(["a truck", "a bus", "a bike", "I was HIT  BY a van"], ["truck", "bus", "hit by"]) == [1, 1, 0, 1]


def test_empty_rows_noted_and_confidence_is_one():
    labels = match_keywords(["", "   ", "car"], ["car"])
    assert labels[0].note == Note.EMPTY and labels[1].note == Note.EMPTY and labels[0].label is None
    assert labels[2].label == 1 and labels[2].confidence == 1.0


def test_run_keyword_query_stats_and_no_cost():
    result = run_keyword_query(["my car", "a scar", "", "truck"], "car, truck")
    assert [r.label for r in result.labels] == [1, 0, None, 1]
    assert result.stats.matched == 2 and result.stats.not_labelled == 1
    assert result.stats.cost_usd == 0 and result.stats.requests_sent == 0
