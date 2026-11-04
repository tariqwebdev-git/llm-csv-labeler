"""UI tests with Streamlit AppTest. OpenAI is replaced by FakeClassifier (no cost)."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import ui.query_section as query_section
from labeler import labeling_engine
from tests.fake_classifier import FakeClassifier

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = (ROOT / "sample_data" / "sample.csv").read_bytes()


@pytest.fixture
def make_app(monkeypatch, tmp_path):
    """Build an AppTest with a temp cache, a fake model and a chosen key state."""
    monkeypatch.setattr("labeler.config.CACHE_PATH", tmp_path / "cache.db")
    fake = FakeClassifier()
    real_run = labeling_engine.run_query
    monkeypatch.setattr(query_section, "run_query",
                        lambda texts, query, **kw: real_run(texts, query, **{**kw, "classifier": fake}))

    def build(api_key: str | None = "test-key") -> AppTest:
        monkeypatch.setattr("labeler.api_key.load_api_key", lambda: api_key)
        at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30)
        return at.run()

    return build


def _upload(at: AppTest, data: bytes = SAMPLE, name: str = "sample.csv") -> AppTest:
    at.file_uploader[0].set_value((name, data, "text/csv"))
    return at.run()


def test_upload_shows_preview_and_picks_text_column(make_app):
    at = _upload(make_app())
    assert not at.exception
    assert "220 rows" in at.markdown[0].value
    assert at.selectbox(key="text_column_select").value == "transportation_open"


def test_run_disabled_without_key(make_app):
    at = _upload(make_app(api_key=None))
    at.text_area(key="query_text").input("hit by a vehicle").run()
    assert at.button[0].disabled
    assert any("API key missing" in e.value for e in at.sidebar.error)


def test_run_labels_rows_and_shows_counts(make_app):
    at = _upload(make_app())
    at.text_area(key="query_text").input("hit by a vehicle").run()
    assert at.text_input(key="query_name").value == "hit_vehicle"
    at.button[0].click().run()

    assert not at.exception
    state = at.session_state["app_state"]
    assert len(state.result.labels) == 220 and state.result_name == "hit_vehicle"
    assert any("of 220 matched" in i.value for i in at.info)


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
    at.text_area(key="query_text").input("accident").run()
    assert any("Short queries" in w.value for w in at.warning)
