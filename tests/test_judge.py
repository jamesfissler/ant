"""Tests for prompt construction and verdict mapping."""

from __future__ import annotations

from fin_discrim.items import EvalItem
from fin_discrim.judge import (
    SYSTEM_PROMPT,
    _to_preference,
    build_prompt,
    opposite,
)

ITEM = EvalItem(
    item_id="an-idea",
    seed_idea="the seed idea text",
    plan_a="AAA plan a body",
    plan_b="BBB plan b body",
    gold_preference="A",
)


def test_prompt_places_plan_a_first_when_as_is() -> None:
    prompt = build_prompt(ITEM, "as_is")
    assert prompt.index("AAA plan a body") < prompt.index("BBB plan b body")


def test_prompt_places_plan_b_first_when_swapped() -> None:
    prompt = build_prompt(ITEM, "swapped")
    assert prompt.index("BBB plan b body") < prompt.index("AAA plan a body")


def test_prompt_never_leaks_gold_data() -> None:
    """The gold preference and critiques must not reach the model."""
    item = EvalItem(
        item_id="leaky",
        seed_idea="idea",
        plan_a="plan a",
        plan_b="plan b",
        gold_preference="B",
    )
    for order in ("as_is", "swapped"):
        prompt = build_prompt(item, order)
        assert "gold" not in prompt.lower()
        assert "gold" not in SYSTEM_PROMPT.lower()
        # The only A/B labels shown are the neutral Plan 1 / Plan 2 headings.
        assert "Plan A" not in prompt and "Plan B" not in prompt


def test_prompt_contains_seed_idea_and_both_plans() -> None:
    prompt = build_prompt(ITEM, "as_is")
    assert ITEM.seed_idea in prompt
    assert ITEM.plan_a in prompt
    assert ITEM.plan_b in prompt


def test_to_preference_maps_position_back_to_label() -> None:
    assert _to_preference("Plan 1", "as_is") == "A"
    assert _to_preference("Plan 2", "as_is") == "B"
    assert _to_preference("Plan 1", "swapped") == "B"
    assert _to_preference("Plan 2", "swapped") == "A"


def test_opposite_flips_order() -> None:
    assert opposite("as_is") == "swapped"
    assert opposite("swapped") == "as_is"
