"""The dimensions a plan or critique is scored on.

This module is the extension point of the pointwise suite. To add a dimension,
write one :class:`Dimension` and append it to :data:`DIMENSIONS`; nothing else
needs to change. Every dimension shares the same 1-5 scale defined here, so a
new one only has to say what it asks and what separates a high score from a low
one.

Each dimension is scored by its own model call, so adding one cannot change the
scores of the others. That keeps results comparable as the suite grows.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal, get_args

Target = Literal["plan", "critique"]
"""What a dimension judges: the plan itself, or the critique of that plan."""

Score = Literal[1, 2, 3, 4, 5]
SCORES: tuple[int, ...] = get_args(Score)
SCALE_MIN, SCALE_MAX = min(SCORES), max(SCORES)

SCALE = """\
1 - Absent. The submission does not engage with this at all.
2 - Gestured at. Mentioned, but with nothing behind it.
3 - Partial. Genuinely attempted, with a gap that matters.
4 - Solid. Handled well, with a minor gap or an unexamined assumption.
5 - Exemplary. Handled thoroughly, including the cases that usually get missed."""


@dataclass(frozen=True, slots=True)
class Dimension:
    """One scored question, applied to a plan or to a critique."""

    key: str
    """Stable identifier, used in reports and as the expert-score key."""
    target: Target
    title: str
    question: str
    """The question put to the model, answered on the shared 1-5 scale."""
    guidance: str
    """What separates a high score from a low one for this dimension."""


DIMENSIONS: tuple[Dimension, ...] = (
    Dimension(
        key="falsifiability",
        target="plan",
        title="Could it return a no?",
        question=(
            "Could running this plan as written produce a result that would "
            "make a competent researcher abandon the idea?"
        ),
        guidance=(
            "High: the plan names an outcome that would kill the idea, and the "
            "threshold for it is justified rather than asserted. Low: every "
            "outcome can be read as encouraging, the plan assumes the effect is "
            "real and moves to implementation, or the criteria are numbers with "
            "no stated reasoning behind them that could be moved after seeing "
            "results."
        ),
    ),
    Dimension(
        key="kill-order",
        target="plan",
        title="Cheapest disconfirming test first",
        question=(
            "Does the plan order its work so that the cheapest tests capable of "
            "killing the idea run before the expensive ones?"
        ),
        guidance=(
            "High: the decisive, cheap test comes first, and the plan says what "
            "stops if it fails. Low: infrastructure, simulation, or a full "
            "backtest is built before anything could invalidate the premise, or "
            "the plan is a flat list of work with no stopping points. Judge the "
            "ordering, not the total effort."
        ),
    ),
    Dimension(
        key="critique-bite",
        target="critique",
        title="Does the critique bite?",
        question=(
            "Does the critique identify problems that would actually change the "
            "plan, rather than restating it or listing generic caveats?"
        ),
        guidance=(
            "High: it names specific, load-bearing weaknesses and says what "
            "would have to change. Low: it summarises the plan approvingly, "
            "raises only risks any plan would carry, or asks for more work "
            "without saying what the current work fails to establish. A "
            "critique of a strong plan can still score high by finding its real "
            "limits."
        ),
    ),
)

BY_KEY: Mapping[str, Dimension] = MappingProxyType({d.key: d for d in DIMENSIONS})


def select(keys: Sequence[str] | None) -> tuple[Dimension, ...]:
    """The requested dimensions in registry order, or all of them.

    Raises ValueError naming the unknown keys, so a typo fails before any API
    call rather than silently narrowing a run.
    """
    if not keys:
        return DIMENSIONS
    unknown = [key for key in keys if key not in BY_KEY]
    if unknown:
        raise ValueError(
            f"unknown dimension(s): {', '.join(unknown)}; "
            f"available: {', '.join(BY_KEY)}"
        )
    wanted = set(keys)
    return tuple(d for d in DIMENSIONS if d.key in wanted)
