from ui.page_style import _CSS_FILE


def test_css_has_no_less_than_sign():
    """Streamlit drops a whole <style> block whose text contains '<', so the bars would stop working."""
    assert "<" not in _CSS_FILE.read_text(encoding="utf-8")


def test_css_targets_the_bars_used_in_app():
    css = _CSS_FILE.read_text(encoding="utf-8")
    assert ".st-key-top_bar" in css and ".st-key-bottom_bar" in css and ".st-key-query_area" in css
