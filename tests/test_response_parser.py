import math

from labeler.models import TokenLogprob
from labeler.response_parser import parse_reply


def _tok(text, top=None):
    return TokenLogprob(text, top or {})


def _answer(digit, p):
    other = "0" if digit == "1" else "1"
    return _tok(digit, {digit: math.log(p), other: math.log(1 - p)})


def test_parses_lines_and_confidence():
    tokens = [_tok("1"), _tok("|"), _answer("1", 0.8), _tok("\n"), _tok("2"), _tok("|"), _answer("0", 0.99)]
    content = "".join(t.token for t in tokens)
    result = parse_reply(content, tokens, batch_size=2)
    assert result[1].label == 1 and result[1].confidence == 0.8
    assert result[2].label == 0 and result[2].confidence == 0.99


def test_merged_token_gives_label_without_confidence():
    tokens = [_tok("1"), _tok("|1")]
    result = parse_reply("1|1", tokens, batch_size=1)
    assert result[1].label == 1 and result[1].confidence is None


def test_ignores_unknown_ids_garbage_and_duplicates():
    content = "1|1\n1|0\n9|1\nhello\n2|yes\n"
    result = parse_reply(content, [], batch_size=2)
    assert list(result) == [1]
    assert result[1].label == 1          # first answer kept


def test_tolerates_spaces():
    assert parse_reply("  3 | 0 ", [], batch_size=3)[3].label == 0
