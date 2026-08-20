"""Loading of discriminator evaluation items from JSON files on disk.

An evaluation item pairs one seed research idea with two competing research
plans, plus the gold-standard judgements held back for scoring. Nothing in this
module decides what is sent to a model; see :mod:`fin_discrim.judge`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Preference = Literal["A", "B"]

_PREFERENCE_ALIASES: dict[str, Preference] = {
    "a": "A",
    "plan_a": "A",
    "plan a": "A",
    "b": "B",
    "plan_b": "B",
    "plan b": "B",
}


@dataclass(frozen=True, slots=True)
class EvalItem:
    """One seed idea with the two plans to be discriminated between."""

    item_id: str
    seed_idea: str
    plan_a: str
    plan_b: str
    gold_preference: Preference | None
    """The held-back correct answer. ``None`` when the item is unlabelled."""

    @property
    def is_labelled(self) -> bool:
        return self.gold_preference is not None


def parse_preference(raw: str) -> Preference | None:
    """Normalise a gold preference string; empty/whitespace means unlabelled."""
    text = raw.strip().lower()
    if not text:
        return None
    try:
        return _PREFERENCE_ALIASES[text]
    except KeyError:
        raise ValueError(
            f"unrecognised gold_preference {raw!r}; expected one of "
            f"{sorted(_PREFERENCE_ALIASES)} or an empty string"
        ) from None


def load_item(path: Path) -> EvalItem:
    """Read a single eval item, raising ValueError on a malformed file."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        # A malformed data file is a value problem, not a caller type error.
        raise ValueError(  # noqa: TRY004
            f"{path}: expected a JSON object, got {type(payload).__name__}"
        )

    def field(name: str) -> str:
        try:
            value = payload[name]
        except KeyError:
            raise ValueError(f"{path}: missing required field {name!r}") from None
        if not isinstance(value, str):
            raise ValueError(f"{path}: field {name!r} must be a string")  # noqa: TRY004
        return value

    for name in ("seed_idea", "plan_A", "plan_B"):
        if not field(name).strip():
            raise ValueError(f"{path}: field {name!r} is empty")

    try:
        gold = parse_preference(field("gold_preference"))
    except ValueError as exc:
        raise ValueError(f"{path}: {exc}") from None

    return EvalItem(
        item_id=path.stem,
        seed_idea=field("seed_idea"),
        plan_a=field("plan_A"),
        plan_b=field("plan_B"),
        gold_preference=gold,
    )


def load_items(directory: Path) -> list[EvalItem]:
    """Read every ``*.json`` file in ``directory``, sorted by filename."""
    if not directory.is_dir():
        raise ValueError(f"{directory}: not a directory")
    paths = sorted(directory.glob("*.json"))
    if not paths:
        raise ValueError(f"{directory}: contains no .json eval items")
    return [load_item(path) for path in paths]
