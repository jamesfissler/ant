"""Tests for scoring verdicts against gold preferences."""

from __future__ import annotations

from fin_discrim.items import EvalItem, Preference
from fin_discrim.judge import Judgement, JudgementFailure, PresentationOrder
from fin_discrim.scoring import score_all, score_model


def item(item_id: str, gold: Preference | None) -> EvalItem:
    return EvalItem(
        item_id=item_id,
        seed_idea="idea",
        plan_a="a",
        plan_b="b",
        gold_preference=gold,
    )


def judgement(
    item_id: str,
    model: str,
    preference: Preference,
    order: PresentationOrder = "as_is",
) -> Judgement:
    return Judgement(
        item_id=item_id,
        model=model,
        order=order,
        preference=preference,
        confidence="high",
        reasoning="because",
        input_tokens=10,
        output_tokens=5,
    )


def test_accuracy_counts_only_labelled_items() -> None:
    items = [item("one", "A"), item("two", "B"), item("three", None)]
    results = [
        judgement("one", "m", "A"),
        judgement("two", "m", "A"),
        judgement("three", "m", "A"),
    ]
    (score,) = score_all(["m"], list(results), items)
    assert score.judged == 3
    assert score.scored == 2
    assert score.correct == 1
    assert score.accuracy == 0.5
    assert score.chose_a == 3
    assert score.chose_b == 0


def test_accuracy_is_none_without_gold_labels() -> None:
    items = [item("one", None)]
    (score,) = score_all(["m"], [judgement("one", "m", "A")], items)
    assert score.scored == 0
    assert score.accuracy is None


def test_failures_are_counted_separately_from_judgements() -> None:
    items = [item("one", "A"), item("two", "A")]
    results = [
        judgement("one", "m", "A"),
        JudgementFailure(item_id="two", model="m", order="as_is", error="boom"),
    ]
    (score,) = score_all(["m"], list(results), items)
    assert score.judged == 1
    assert score.failed == 1
    assert score.accuracy == 1.0


def test_first_position_rate_tracks_the_shown_order() -> None:
    items = [item("one", "A"), item("two", "A")]
    results = [
        judgement("one", "m", "A", "as_is"),  # A shown first, picked first
        judgement("two", "m", "A", "swapped"),  # B shown first, picked second
    ]
    (score,) = score_all(["m"], list(results), items)
    assert score.first_shown == 1
    assert score.first_position_rate == 0.5


def test_order_flip_detected_when_answer_changes_with_position() -> None:
    items = [item("one", "A"), item("two", "A")]
    results = [
        # Consistent: picks A in both orders.
        judgement("one", "m", "A", "as_is"),
        judgement("one", "m", "A", "swapped"),
        # Position-biased: always picks whatever came first.
        judgement("two", "m", "A", "as_is"),
        judgement("two", "m", "B", "swapped"),
    ]
    (score,) = score_all(["m"], list(results), items)
    assert score.agreement_pairs == 2
    assert score.order_flips == 1
    assert score.flip_rate == 0.5


def test_single_order_run_reports_no_flip_rate() -> None:
    items = [item("one", "A")]
    (score,) = score_all(["m"], [judgement("one", "m", "A")], items)
    assert score.agreement_pairs == 0
    assert score.flip_rate is None


def test_models_are_scored_independently() -> None:
    items = [item("one", "A")]
    results = [judgement("one", "fast", "A"), judgement("one", "slow", "B")]
    fast, slow = score_all(["fast", "slow"], list(results), items)
    assert fast.accuracy == 1.0
    assert slow.accuracy == 0.0
    assert score_model("fast", list(results), {"one": "A"}).judged == 1
