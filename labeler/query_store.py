"""Save queries to JSON and load them back (to reuse on a new CSV)."""
import json
from collections.abc import Iterable

from labeler.column_utils import to_column_name, unique_column_name
from labeler.errors import QueryFileError
from labeler.models import Query

FORMAT_VERSION = 1


def queries_to_json(queries: Iterable[Query]) -> str:
    data = {
        "version": FORMAT_VERSION,
        "queries": [{"name": q.name, "text": q.text} for q in queries],
    }
    return json.dumps(data, indent=2, ensure_ascii=False)


def queries_from_json(text: str, existing_names: Iterable[str] = ()) -> list[Query]:
    """Parse a query file into new 'Not run' queries.

    Names clashing with `existing_names` (or each other) get _2, _3, ...
    Raises QueryFileError with a plain message if the file is invalid.
    """
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise QueryFileError("The query file is not valid JSON.") from exc

    if not isinstance(data, dict) or data.get("version") != FORMAT_VERSION:
        raise QueryFileError(f"Unsupported query file (expected version {FORMAT_VERSION}).")
    items = data.get("queries")
    if not isinstance(items, list):
        raise QueryFileError("The query file has no 'queries' list.")

    taken = set(existing_names)
    queries: list[Query] = []
    for item in items:
        if not isinstance(item, dict) or not str(item.get("text", "")).strip():
            raise QueryFileError("Every query needs a 'name' and a non-empty 'text'.")
        query_text = str(item["text"]).strip()
        name = unique_column_name(to_column_name(str(item.get("name") or query_text)), taken)
        taken.add(name)
        queries.append(Query(name=name, text=query_text))
    return queries
