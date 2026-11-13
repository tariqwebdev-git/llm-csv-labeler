import pytest

from labeler.errors import QueryFileError
from labeler.models import Query, QueryStatus
from labeler.query_store import queries_from_json, queries_to_json


def test_round_trip_loads_as_not_run():
    text = queries_to_json([Query("kids", "Stories about children", QueryStatus.DONE)])
    loaded = queries_from_json(text)
    assert [(q.name, q.text, q.status) for q in loaded] == [("kids", "Stories about children", QueryStatus.NOT_RUN)]


def test_duplicate_names_renamed():
    text = queries_to_json([Query("kids", "a"), Query("kids", "b")])
    assert [q.name for q in queries_from_json(text, existing_names={"kids"})] == ["kids_2", "kids_3"]


@pytest.mark.parametrize("bad", ["not json", '{"version": 2, "queries": []}', '{"version": 1}',
                                 '{"version": 1, "queries": [{"name": "x"}]}'])
def test_invalid_files_rejected(bad):
    with pytest.raises(QueryFileError):
        queries_from_json(bad)


def test_keyword_kind_round_trips_and_old_files_load_as_llm():
    from labeler.models import Query, QueryKind
    from labeler.query_store import queries_from_json, queries_to_json
    saved = queries_to_json([Query("vehicles", "car, truck*", kind=QueryKind.KEYWORD)])
    loaded = queries_from_json(saved)[0]
    assert (loaded.kind, loaded.text) == (QueryKind.KEYWORD, "car, truck*")
    old = queries_from_json('{"version": 1, "queries": [{"name": "kids", "text": "Stories about children"}]}')[0]
    assert old.kind == QueryKind.LLM
