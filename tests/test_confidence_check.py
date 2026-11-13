"""Claude-style confidence: stated certainty, vote check on doubtful rows, calibration (no API cost)."""
from labeler import config
from labeler.confidence_check import calibrate, combine_votes, finalize, is_doubtful
from labeler.labeling_engine import estimate_cost, run_query
from labeler.models import Note, Provider, RowLabel
from labeler.prompt_builder import SCORED_SYSTEM_PROMPT, SYSTEM_PROMPT
from labeler.response_parser import parse_reply
from tests.fake_classifier import FakeClassifier, contains_hit


# --- parser ---------------------------------------------------------------------------
def test_parser_reads_stated_certainty_and_clamps_it():
    result = parse_reply("1|1|85\n2|0|30\n3|1|100\n4|0", [], batch_size=4)
    assert [(r.label, r.confidence) for r in result.values()] == [(1, 0.85), (0, 0.5), (1, 1.0), (0, None)]


# --- combining votes ------------------------------------------------------------------
def test_unanimous_sure_votes_give_high_confidence():
    final = combine_votes(RowLabel(1, 0.7), [RowLabel(1, 0.9)] * 4)
    assert final.label == 1 and final.confidence == round((1.0 + (0.7 + 0.9 * 4) / 5) / 2, 2)


def test_majority_wins_and_flip_flopping_is_low():
    final = combine_votes(RowLabel(1, 0.6), [RowLabel(0, 0.9), RowLabel(0, 0.9), RowLabel(1, 0.6), RowLabel(0, 0.9)])
    assert final.label == 0 and final.confidence < 0.8          # 3 of 5 agreed


def test_tie_keeps_first_answer():
    assert combine_votes(RowLabel(1, 0.6), [RowLabel(0, 0.6), RowLabel(1, 0.6), RowLabel(0, 0.6)]).label == 1


def test_failed_rechecks_never_guess():
    first = RowLabel(1, 0.6)
    assert combine_votes(first, [RowLabel(note=Note.FAILED)] * 4).label == 1
    assert combine_votes(RowLabel(note=Note.REFUSED), [RowLabel(note=Note.FAILED)]).label is None


def test_calibration_table_interpolates_and_clamps():
    table = [(0.5, 0.5), (0.8, 0.6), (1.0, 0.95)]
    assert calibrate(0.65, table) == 0.55 and abs(calibrate(0.9, table) - 0.775) <= 0.006   # halfway point
    assert calibrate(0.3, table) == 0.5 and calibrate(1.2, table) == 0.95
    assert calibrate(0.73) == 0.73                               # identity until calibrated


def test_doubtful_and_finalize():
    assert is_doubtful(RowLabel(1, 0.7)) and is_doubtful(RowLabel(1, None))
    assert not is_doubtful(RowLabel(1, 0.9)) and not is_doubtful(RowLabel(note=Note.REFUSED))
    assert finalize(RowLabel(1, 0.9)).confidence == 0.9


# --- the whole run, Claude style --------------------------------------------------------
def _claude_run(texts, fake, cache_path):
    return run_query(texts, "hit by a vehicle", classifier=fake, provider=Provider.ANTHROPIC, cache_path=cache_path)


def test_only_doubtful_rows_are_rechecked_and_shuffled(tmp_path):
    unsure = {"maybe hit 1", "maybe hit 2", "maybe hit 3"}
    fake = FakeClassifier(score=lambda t: 60 if t in unsure else 95)
    texts = ["a car hit me", "the bus was late"] + sorted(unsure)
    result = _claude_run(texts, fake, tmp_path / "c.db")
    first_pass, rechecks = fake.calls[0], fake.calls[1:]
    assert len(first_pass) == 5 and len(rechecks) == config.VOTE_CHECK_ROUNDS
    assert all(set(call) == unsure for call in rechecks)                    # only the doubtful rows
    assert len({tuple(call) for call in rechecks}) > 1                      # in different orders
    assert all("<50-100>" in prompt for prompt in fake.system_prompts)
    assert result.labels[0].confidence == 0.95                              # sure row: its own rating
    assert all(r.label == 1 and r.confidence is not None for r in result.labels[2:])
    assert result.stats.requests_sent == 1 + config.VOTE_CHECK_ROUNDS


def test_combined_result_is_cached_and_rerun_is_free(tmp_path):
    cache = tmp_path / "c.db"
    texts = ["a car hit me", "maybe hit"]
    first = _claude_run(texts, FakeClassifier(score=lambda t: 60 if "maybe" in t else 95), cache)
    again = FakeClassifier(score=lambda t: 95)
    second = _claude_run(texts, again, cache)
    assert again.calls == [] and second.stats.cost_usd == 0
    assert [r.confidence for r in second.labels] == [r.confidence for r in first.labels]


def test_flip_flopping_row_gets_majority_label_and_low_confidence(tmp_path):
    answers = iter(["1", "0", "0", "1", "0"])                                # 3 of 5 say 0
    fake = FakeClassifier(answer=lambda t: next(answers), score=lambda t: 60)
    result = _claude_run(["unclear"], fake, tmp_path / "c.db")
    assert result.labels[0].label == 0 and result.labels[0].confidence < 0.7


def test_openai_runs_are_unchanged(tmp_path):
    fake = FakeClassifier()
    result = run_query(["a car hit me", "late bus"], "hit by a vehicle", classifier=fake, cache_path=tmp_path / "c.db")
    assert len(fake.calls) == 1 and fake.system_prompts == [SYSTEM_PROMPT]
    assert [r.label for r in result.labels] == [int(contains_hit(t)) for t in ["a car hit me", "late bus"]]
    assert SCORED_SYSTEM_PROMPT != SYSTEM_PROMPT


def test_claude_estimate_includes_rechecks(tmp_path):
    texts = [f"answer number {i}" for i in range(40)]
    openai = estimate_cost(texts, "hit by a vehicle", cache_path=tmp_path / "c.db")
    claude = estimate_cost(texts, "hit by a vehicle", provider=Provider.ANTHROPIC, cache_path=tmp_path / "c.db")
    factor = 1 + config.VOTE_CHECK_SHARE_ESTIMATE * config.VOTE_CHECK_ROUNDS
    assert claude.input_tokens > openai.input_tokens * (factor - 0.05)
