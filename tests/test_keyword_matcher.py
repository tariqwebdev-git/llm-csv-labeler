from labeler.keyword_matcher import match_keywords, parse_keywords
from labeler.labeling_engine import run_keyword_query
from labeler.models import Note


def test_parse_keywords_splits_trims_and_drops_duplicates():
    assert parse_keywords(" car,Truck,, CAR ;hit   by\nbus ") == ["car", "Truck", "hit by", "bus"]


def test_case_is_ignored():
    assert [r.label for r in match_keywords(["My CAR", "my car", "bike"], ["Car"], True)] == [1, 1, 0]


def test_whole_words_on_and_off():
    assert match_keywords(["a scar on my arm"], ["car"], whole_words=True)[0].label == 0
    assert match_keywords(["a scar on my arm"], ["car"], whole_words=False)[0].label == 1
    assert match_keywords(["car-free street", "cars."], ["car"], True)[0].label == 1   # punctuation is a boundary


def test_phrase_matches_any_spacing():
    labels = match_keywords(["I was HIT  BY a bus", "hit the brakes by the bus"], ["hit by"], True)
    assert [r.label for r in labels] == [1, 0]


def test_empty_rows_noted_and_confidence_is_one():
    labels = match_keywords(["", "   ", "car"], ["car"], True)
    assert labels[0].note == Note.EMPTY and labels[1].note == Note.EMPTY and labels[0].label is None
    assert labels[2].label == 1 and labels[2].confidence == 1.0


def test_run_keyword_query_stats_and_no_cost():
    result = run_keyword_query(["my car", "a scar", "", "truck"], "car, truck")
    assert [r.label for r in result.labels] == [1, 0, None, 1]
    assert result.stats.matched == 2 and result.stats.not_labelled == 1
    assert result.stats.cost_usd == 0 and result.stats.requests_sent == 0
