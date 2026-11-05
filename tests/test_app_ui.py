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
        monkeypatch.setattr("labeler.api_key.load_api_key", lambda: api_key)
        return AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()

    return build


def _upload(at: AppTest, data: bytes = SAMPLE, name: str = "sample.csv") -> AppTest:
    at.file_uploader[0].set_value((name, data, "text/csv"))
    return at.run()


def _add(at: AppTest, text: str) -> AppTest:
    at.text_area(key="new_query_text").input(text).run()
    return at.button(key="add_query").click().run()


def _state(at: AppTest):
    return at.session_state["app_state"]


def _click(at: AppTest, kind: str, index: int = 0) -> AppTest:
    query_id = _state(at).queries[index].id
    return at.button(key=f"{kind}_{query_id}").click().run()


def test_upload_shows_preview_and_picks_text_column(make_app):
    at = _upload(make_app())
    assert not at.exception
    assert "220 rows" in at.markdown[0].value
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
    assert any("API key missing" in e.value for e in at.sidebar.error)


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
    at.text_area(key="new_query_text").input("accident").run()
    assert any("Short queries" in w.value for w in at.warning)


def test_card_shows_test_and_full_estimates(make_app):
    at = _add(_upload(make_app()), "Mentions a person hit by a vehicle")
    assert any("test $" in c.value and "for 20 rows" in c.value and "full run $" in c.value for c in at.caption)
