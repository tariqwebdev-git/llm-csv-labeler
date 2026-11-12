"""Confidence for models without token probabilities (Claude).

Each row first gets the model's own certainty (50-100). Rows below
config.VOTE_CHECK_BELOW are asked again a few times; the majority answer wins,
and the confidence combines how many votes agreed with how sure those votes were.
Finally a calibration table (config.CLAUDE_CONFIDENCE_CALIBRATION) turns the raw
number into "how often rows like this are actually right".

Logic only: no API calls here (the engine sends the re-checks).
"""
from collections import Counter

from labeler import config
from labeler.models import RowLabel

_MIN_CONFIDENCE, _MAX_CONFIDENCE = 0.5, 1.0


def is_doubtful(label: RowLabel, below: float = config.VOTE_CHECK_BELOW) -> bool:
    """A labelled row whose stated certainty is under `below` (or missing)."""
    return label.label is not None and (label.confidence is None or label.confidence < below)


def calibrate(raw: float, table: list[tuple[float, float]] | None = None) -> float:
    """Map a raw confidence through the calibration table (straight lines between points)."""
    points = sorted(table or config.CLAUDE_CONFIDENCE_CALIBRATION)
    if raw <= points[0][0]:
        value = points[0][1]
    elif raw >= points[-1][0]:
        value = points[-1][1]
    else:
        value = points[-1][1]
        for (x0, y0), (x1, y1) in zip(points, points[1:]):
            if x0 <= raw <= x1:
                value = y0 + (y1 - y0) * (raw - x0) / (x1 - x0)
                break
    return round(min(max(value, _MIN_CONFIDENCE), _MAX_CONFIDENCE), 2)


def finalize(label: RowLabel) -> RowLabel:
    """A row that needed no re-check: its stated certainty, calibrated."""
    if label.label is None or label.confidence is None:
        return label
    return RowLabel(label=label.label, confidence=calibrate(label.confidence), note=label.note)


def combine_votes(first: RowLabel, votes: list[RowLabel]) -> RowLabel:
    """Final label and confidence from the first answer plus the re-check answers.

    - Only answered votes count (refused or failed re-checks are ignored).
    - The majority label wins; a tie keeps the first answer (never a guess).
    - Raw confidence = average of (share of votes for that label) and (mean stated
      certainty of those votes), then calibrated. A row the model flip-flops on
      always ends up low, even if each answer claimed to be sure.
    """
    valid = [v for v in (first, *votes) if v.label is not None]
    if not valid:
        return first
    counts = Counter(v.label for v in valid)
    top = counts.most_common()
    label = top[0][0]
    if len(top) > 1 and top[0][1] == top[1][1] and first.label is not None:
        label = first.label
    agreeing = [v for v in valid if v.label == label]
    share = len(agreeing) / len(valid)
    scores = [v.confidence for v in agreeing if v.confidence is not None]
    certainty = sum(scores) / len(scores) if scores else share
    return RowLabel(label=label, confidence=calibrate((share + certainty) / 2), note=first.note)
