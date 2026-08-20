"""Loading of discriminator evaluation items from JSON files on disk.

An evaluation item pairs one seed research idea with two competing research
plans, plus the gold-standard judgements held back for scoring. Nothing in this
module decides what is sent to a model; see :mod:`fin_discrim.judge`.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

Preference = Literal["A", "B"]
Side = Literal["A", "B"]
"""Which of an item's two submissions a pointwise assessment is about."""

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
    critique_a: str = ""
    critique_b: str = ""
    """Each plan's self-critique. Empty for items written before they existed."""
    expert_scores_a: Mapping[str, int] = field(default_factory=dict)
    expert_scores_b: Mapping[str, int] = field(default_factory=dict)
    """Held-back per-dimension expert scores, keyed by dimension. Usually empty:
    pointwise assessment reports model scores alone until these are filled in."""

    @property
    def is_labelled(self) -> bool:
        return self.gold_preference is not None

    def plan(self, side: Side) -> str:
        """The plan under assessment on this side."""
        return self.plan_a if side == "A" else self.plan_b

    def critique(self, side: Side) -> str:
        """The self-critique of this side's plan."""
        return self.critique_a if side == "A" else self.critique_b

    def expert_scores(self, side: Side) -> Mapping[str, int]:
        """Expert scores held for this side, empty when none were recorded."""
        return self.expert_scores_a if side == "A" else self.expert_scores_b


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

    def text(name: str) -> str:
        try:
            value = payload[name]
        except KeyError:
            raise ValueError(f"{path}: missing required field {name!r}") from None
        if not isinstance(value, str):
            raise ValueError(f"{path}: field {name!r} must be a string")  # noqa: TRY004
        return value

    for name in ("seed_idea", "plan_A", "plan_B"):
        if not text(name).strip():
            raise ValueError(f"{path}: field {name!r} is empty")

    def optional_text(name: str) -> str:
        """A field absent from older items; missing reads as empty, not an error."""
        value = payload.get(name, "")
        if not isinstance(value, str):
            raise ValueError(f"{path}: field {name!r} must be a string")  # noqa: TRY004
        return value

    def scores(name: str) -> dict[str, int]:
        """Expert scores for one side. Dimension keys are checked by whichever
        evaluation suite consumes them, not here."""
        value = payload.get(name, {})
        if not isinstance(value, dict):
            raise ValueError(  # noqa: TRY004
                f"{path}: field {name!r} must be a JSON object of dimension scores"
            )
        parsed: dict[str, int] = {}
        for key, raw in value.items():
            if isinstance(raw, bool) or not isinstance(raw, int):
                raise ValueError(  # noqa: TRY004
                    f"{path}: expert score {name}[{str(key)!r}] must be an integer"
                )
            parsed[str(key)] = raw
        return parsed

    try:
        gold = parse_preference(text("gold_preference"))
    except ValueError as exc:
        raise ValueError(f"{path}: {exc}") from None

    return EvalItem(
        item_id=path.stem,
        seed_idea=text("seed_idea"),
        plan_a=text("plan_A"),
        plan_b=text("plan_B"),
        gold_preference=gold,
        critique_a=optional_text("critique_A"),
        critique_b=optional_text("critique_B"),
        expert_scores_a=scores("expert_scores_A"),
        expert_scores_b=scores("expert_scores_B"),
    )


def load_items(directory: Path) -> list[EvalItem]:
    """Read every ``*.json`` file in ``directory``, sorted by filename."""
    if not directory.is_dir():
        raise ValueError(f"{directory}: not a directory")
    paths = sorted(directory.glob("*.json"))
    if not paths:
        raise ValueError(f"{directory}: contains no .json eval items")
    return [load_item(path) for path in paths]
