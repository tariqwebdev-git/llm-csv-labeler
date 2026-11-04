import pandas as pd

from labeler.column_utils import (
    column_with_fewest_empty,
    count_empty,
    guess_text_column,
    suggest_column_name,
    to_column_name,
    unique_column_name,
)


def test_to_column_name():
    assert to_column_name("  Car Crashes! (2024) ") == "car_crashes_2024"
    assert to_column_name("!!!") == "query"


def test_unique_column_name():
    assert unique_column_name("kids", {"kids", "kids_2"}) == "kids_3"
    assert unique_column_name("kids", set()) == "kids"


def test_suggest_column_name():
    assert suggest_column_name("Mentions a person getting hit by a car") == "person_getting_hit"


def test_guess_text_column_picks_longest():
    df = pd.DataFrame({"id": ["1", "2"], "short": ["ok", "no"], "long": ["a long answer here", "another long one"]})
    assert guess_text_column(df) == "long"


def test_count_empty_and_best_column():
    df = pd.DataFrame({"a": ["", "  ", "x", "|"], "b": ["t", "t", "t", ""]})
    assert count_empty(df, "a") == 3          # blank, spaces and a lone pipe are all empty
    assert column_with_fewest_empty(df) == "b"
