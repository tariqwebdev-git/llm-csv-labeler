import pandas as pd

from ui.answer_table import white_cells


def test_white_cells_and_green_matches():
    df = pd.DataFrame({"text": ["a", "b"], "q": ["1", "0"]})
    styles = white_cells(df, match_column="q")._compute().ctx
    first_row = dict(styles[(0, 0)])
    second_row = dict(styles[(1, 0)])
    assert first_row["background-color"] == "#d9f2e1"           # matched row: light green
    assert second_row["background-color"] == "#ffffff"          # others: white
    assert first_row["color"] == second_row["color"] == "#31333f"   # dark text in any theme


def test_white_cells_without_matches():
    styles = white_cells(pd.DataFrame({"text": ["a"]}))._compute().ctx
    assert dict(styles[(0, 0)])["background-color"] == "#ffffff"
