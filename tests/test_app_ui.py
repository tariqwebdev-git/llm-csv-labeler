"""UI tests with Streamlit AppTest. OpenAI is replaced by FakeClassifier (no cost)."""
import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import ui.query_card as query_card
from labeler import labeling_engine
from labeler.models import QueryStatus
from tests.fake_classifier import FakeClassifier
from ui.download_section import labeled_table

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = (ROOT / "sample_data" / "sample.csv").read_bytes()


@pytest.fixture
def make_app(monkeypatch, tmp_path):
    """Build an AppTest with a temp cache, a fake model and a chosen key state."""
    monkeypatch.setattr("labeler.config.CACHE_PATH", tmp_path / "cache.db")
    fake = FakeClassifier()
    real_run = labeling_engine.run_query
    monkeypatch.setattr(query_card, "run_query",
                        lambda texts, query, **kw: real_run(texts, query, **{**kw, "classifier": fake}))

    def build(api_key: str | None = "test-key") -> AppTest:
        monkeypatch.setattr("labeler.api_key.load_api_key", lambda provider=None: api_key)
        return AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()

    return build


def _upload(at: AppTest, data: bytes = SAMPLE, name: str = "sample.csv") -> AppTest:
    at.file_uploader[0].set_value((name, data, "text/csv"))
    return at.run()


def _add(at: AppTest, text: str) -> AppTest:
    at.text_input(key="new_query_text").input(text).run()
    return at.button(key="add_query").click().run()


def _state(at: AppTest):
    return at.session_state["app_state"]


def _click(at: AppTest, kind: str, index: int = 0) -> AppTest:
    query_id = _state(at).queries[index].id
    return at.button(key=f"{kind}_{query_id}").click().run()


def test_upload_shows_preview_and_picks_text_column(make_app):
    at = _upload(make_app())
    assert not at.exception
    assert any("220 rows" in e.label for e in at.expander)        # data preview header
    assert at.selectbox(key="text_column_select").value == "transportation_open"


def test_add_two_queries_as_cards(make_app):
    at = _add(_add(_upload(make_app()), "Mentions a person hit by a vehicle"), "Mentions buses being late")
    names = [q.name for q in _state(at).queries]
    assert names == ["person_hit_vehicle", "buses_being_late"]
    assert not at.exception


def test_run_disabled_without_key(make_app):
    at = _add(_upload(make_app(api_key=None)), "Mentions a person hit by a vehicle")
    query_id = _state(at).queries[0].id
    assert at.button(key=f"run_{query_id}").disabled
    assert at.button(key=f"test_{query_id}").disabled
    assert any("API key missing" in e.value for e in at.error)


def test_test_run_uses_20_rows(make_app):
    at = _click(_add(_upload(make_app()), "Mentions a person hit by a vehicle"), "test")
    state = _state(at)
    query = state.queries[0]
    assert len(state.test_runs[query.id].result.labels) == 20
    assert query.status == QueryStatus.TESTED


def test_full_run_counts_box_and_download(make_app):
    at = _add(_upload(make_app()), "Mentions a person hit by a vehicle")
    at = _add(at, "Mentions buses being late")
    at = _click(_click(at, "run", 0), "run", 1)
    assert not at.exception
    state = _state(at)
    assert all(q.status == QueryStatus.DONE for q in state.queries)
    assert any("of 220 matched" in i.value for i in at.info)
    table = labeled_table(state)
    assert len(table) == 220
    assert {"person_hit_vehicle", "person_hit_vehicle_conf", "buses_being_late_note"} <= set(table.columns)


def test_edit_marks_out_of_date(make_app):
    at = _click(_add(_upload(make_app()), "Mentions a person hit by a vehicle"), "run")
    at = _click(at, "edit")
    query_id = _state(at).queries[0].id
    at.text_area(key=f"edit_text_{query_id}").input("Mentions a person hit by a car").run()
    at = at.button(key=f"save_{query_id}").click().run()
    assert _state(at).queries[0].status == QueryStatus.OUT_OF_DATE
    assert "person_hit_vehicle" not in labeled_table(_state(at)).columns


def test_delete_needs_confirmation(make_app):
    at = _click(_add(_upload(make_app()), "Mentions a person hit by a vehicle"), "delete")
    assert len(_state(at).queries) == 1               # not yet deleted
    at = _click(at, "confirm_yes")
    assert _state(at).queries == []


def test_load_queries_json_adds_not_run_cards(make_app):
    at = _upload(make_app())
    payload = json.dumps({"version": 1, "queries": [{"name": "kids", "text": "Stories about children"}]})
    at.file_uploader(key="load_queries").set_value(("q.json", payload.encode(), "application/json"))
    at = at.run()
    queries = _state(at).queries
    assert [(q.name, q.status) for q in queries] == [("kids", QueryStatus.NOT_RUN)]


def test_bad_csv_shows_error_not_crash(make_app):
    at = _upload(make_app(), data=b"a,b\n", name="empty.csv")
    assert not at.exception
    assert any("no data rows" in e.value for e in at.error)


def test_empty_rows_warning_names_better_column(make_app):
    data = b"id,notes,answer\n1,,long answer one\n2,,long answer two\n3,x,long answer three\n"
    at = _upload(make_app(), data=data, name="mixed.csv")
    at.selectbox(key="text_column_select").select("notes").run()
    assert any("2 of 3 rows are empty" in e.value and "`answer`" in e.value for e in at.error)


def test_short_query_warning(make_app):
    at = _upload(make_app())
    at.text_input(key="new_query_text").input("accident").run()
    assert any("Short queries" in w.value for w in at.warning)


def test_card_shows_test_and_full_estimates(make_app):
    at = _add(_upload(make_app()), "Mentions a person hit by a vehicle")
    # "$" is escaped, otherwise Streamlit shows the text between two "$" as a maths formula
    assert any("test \\$" in c.value and "for 20 rows" in c.value and "full run \\$" in c.value
               for c in at.caption)


def test_wrong_environment_warning(make_app, monkeypatch):
    import ui.session_info as session_info
    assert not any("own environment" in w.value for w in make_app().warning)
    monkeypatch.setattr(session_info, "running_in_project_env", lambda: False)
    assert any("own environment" in w.value for w in make_app().warning)


def test_query_box_is_one_line_with_hint_as_placeholder(make_app):
    from ui.query_form_section import QUERY_PLACEHOLDER
    at = make_app()
    box = at.text_input(key="new_query_text")
    assert "full sentence" in QUERY_PLACEHOLDER and box.proto.placeholder == QUERY_PLACEHOLDER
    assert not at.text_area                                  # no multi-line box any more


def test_no_big_headers(make_app):
    at = _upload(make_app())
    assert not at.title and not at.header


def test_card_collapses_to_its_name(make_app):
    at = _add(_upload(make_app()), "Mentions a person hit by a vehicle")
    query_id = _state(at).queries[0].id
    assert at.button(key=f"run_{query_id}")                  # open by default
    at = _click(at, "toggle")
    assert not [b for b in at.button if b.key == f"run_{query_id}"]
    assert any("person_hit_vehicle" in m.value for m in at.markdown)
    at = _click(at, "toggle")
    assert at.button(key=f"run_{query_id}")


def test_download_puts_new_columns_after_text_column(make_app):
    at = _add(_upload(make_app()), "Mentions a person hit by a vehicle")
    at = _click(_click(_add(at, "Mentions buses being late"), "run", 0), "run", 1)
    columns = list(labeled_table(_state(at)).columns)
    start = columns.index("transportation_open")
    assert columns[start:start + 7] == [
        "transportation_open",
        "person_hit_vehicle", "person_hit_vehicle_conf", "person_hit_vehicle_note",
        "buses_being_late", "buses_being_late_conf", "buses_being_late_note",
    ]
    assert columns[start + 7] == "housing_open"              # original order kept around them


def test_sidebar_lists_answers_of_chosen_column(make_app):
    at = _upload(make_app())
    assert any("**transportation_open**" in m.value for m in at.sidebar.markdown)
    at.selectbox(key="text_column_select").select("housing_open").run()
    assert any("**housing_open**" in m.value for m in at.sidebar.markdown)
    shown = at.sidebar.dataframe[0].value
    assert list(shown.columns) == ["housing_open"] and (shown["housing_open"].str.strip() != "").all()


def test_old_python_stops_with_message(make_app, monkeypatch):
    monkeypatch.setattr("labeler.python_version_check.python_too_old", lambda: True)
    at = make_app()
    assert any("needs Python 3.12" in e.value for e in at.error)
    assert not [w for w in at.text_input if w.key == "new_query_text"]   # nothing else drawn


def test_switching_column_keeps_each_columns_queries(make_app):
    at = _click(_add(_upload(make_app()), "Mentions a person hit by a vehicle"), "run")
    at.selectbox(key="text_column_select").select("safety_open").run()
    assert _state(at).queries == []
    at = _add(at, "Mentions feeling unsafe at night")
    at.selectbox(key="text_column_select").select("transportation_open").run()
    state = _state(at)
    assert [q.name for q in state.queries] == ["person_hit_vehicle"]
    assert state.queries[0].status == QueryStatus.DONE               # result kept
    columns = list(labeled_table(state).columns)
    assert columns.index("person_hit_vehicle") == columns.index("transportation_open") + 1


def _add_keyword(at: AppTest, words: str, whole_words: bool = True) -> AppTest:
    at.text_input(key="new_keyword_text").input(words).run()
    if not whole_words:
        at.checkbox(key="new_keyword_whole_words").uncheck().run()
    return at.button(key="add_keyword_query").click().run()


def test_keyword_query_runs_without_api_key_and_is_free(make_app):
    import re
    import pandas as pd
    at = _add_keyword(_upload(make_app(api_key=None)), "car, truck, bus")
    query = _state(at).queries[0]
    assert query.name == "car_truck_bus" and query.kind.value == "keyword"
    assert not at.button(key=f"run_{query.id}").disabled
    at = _click(at, "run")
    state = _state(at)
    labels = [r.label for r in state.full_runs[query.id].result.labels]
    texts = pd.read_csv(ROOT / "sample_data" / "sample.csv", dtype=str, keep_default_na=False)["transportation_open"]
    pattern = re.compile(r"(?<!\w)(?:truck|car|bus)(?!\w)", re.IGNORECASE)
    expected = [None if not t.strip() else int(bool(pattern.search(t))) for t in texts]
    assert labels == expected
    assert state.session_spend_usd == 0
    assert any("Free keyword match" in i.value for i in at.info)
    table = labeled_table(state)
    assert set(table["car_truck_bus_conf"]) <= {"1.00", ""}


def test_keyword_edit_whole_words_marks_out_of_date(make_app):
    at = _click(_add_keyword(_upload(make_app()), "car"), "run")
    query_id = _state(at).queries[0].id
    at = _click(at, "edit")
    at.checkbox(key=f"edit_whole_{query_id}").uncheck().run()
    at = at.button(key=f"save_{query_id}").click().run()
    query = _state(at).queries[0]
    assert query.whole_words is False and query.status == QueryStatus.OUT_OF_DATE


def test_sidebar_shows_a_querys_rows_with_filter(make_app):
    at = _click(_add(_upload(make_app()), "Mentions a person hit by a vehicle"), "run")
    state = _state(at)
    query_id = state.queries[0].id
    assert at.button(key=f"sidebar_{query_id}").disabled is False
    at = _click(at, "sidebar")
    assert _state(at).sidebar_query_id == query_id
    assert any("rows of **person_hit_vehicle**" in m.value for m in at.sidebar.markdown)
    matched = state.full_runs[query_id].result.stats.matched
    at.segmented_control(key="sidebar_filter").set_value("Matched").run()
    shown = at.sidebar.dataframe[0].value
    shown = shown.data if hasattr(shown, "data") else shown
    assert len(shown) == matched and set(shown["person_hit_vehicle"]) == {"1"}
    at = at.button(key="sidebar_clear").click().run()
    assert _state(at).sidebar_query_id is None
    assert any("212 answers" in m.value for m in at.sidebar.markdown)


def test_sidebar_button_disabled_before_any_run(make_app):
    at = _add(_upload(make_app()), "Mentions a person hit by a vehicle")
    assert at.button(key=f"sidebar_{_state(at).queries[0].id}").disabled


def test_provider_choice_switches_key_status_and_runs_with_it(make_app, monkeypatch):
    from labeler.models import Provider
    seen = {}
    real = query_card.run_query
    monkeypatch.setattr(query_card, "run_query", lambda texts, query, **kw: (seen.update(kw), real(texts, query, **kw))[1])
    at = _add(_upload(make_app()), "Mentions a person hit by a vehicle")
    assert any("OpenAI key" in m.value for m in at.markdown)
    at.radio(key="provider_choice").set_value(Provider.ANTHROPIC).run()
    assert _state(at).provider == Provider.ANTHROPIC
    assert any("Claude key" in m.value for m in at.markdown)
    assert any("without a confidence score" in c.value for c in at.caption)
    _click(at, "test")
    assert seen["provider"] == Provider.ANTHROPIC
