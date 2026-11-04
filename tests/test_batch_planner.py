from labeler.batch_planner import plan_batches


def test_short_texts_fill_row_limit():
    batches = plan_batches(["short answer"] * 120, max_rows=50, max_tokens=10_000)
    assert [len(b) for b in batches] == [50, 50, 20]


def test_long_texts_split_by_token_budget():
    long_text = "word " * 400            # ~400 tokens
    batches = plan_batches([long_text] * 10, max_rows=50, max_tokens=1_000)
    assert all(len(b) <= 2 for b in batches)
    assert sum(len(b) for b in batches) == 10


def test_oversized_text_gets_its_own_batch():
    huge = "word " * 5_000
    batches = plan_batches(["a", huge, "b"], max_rows=50, max_tokens=1_000)
    assert batches == [[0], [1], [2]]


def test_order_preserved_and_every_index_once():
    texts = ["x " * n for n in (5, 900, 5, 5, 900, 5)]
    batches = plan_batches(texts, max_rows=50, max_tokens=1_000)
    assert [i for b in batches for i in b] == list(range(6))
