"""Scoring model verdicts against the held-back gold preferences."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from fin_discrim.items import EvalItem, Preference
from fin_discrim.judge import Judgement, JudgementFailure, JudgeResult


@dataclass(frozen=True, slots=True)
class ModelScore:
    """One model's performance across the item set."""

    model: str
    judged: int
    failed: int
    chose_a: int
    chose_b: int
    first_shown: int
    """How often the model picked whichever plan was shown first."""
    scored: int
    """Judgements on items that carry a gold preference."""
    correct: int
    agreement_pairs: int
    """Items judged under both presentation orders."""
    order_flips: int
    """Of those, how often the choice changed when the plans were swapped."""

    @property
    def accuracy(self) -> float | None:
        return self.correct / self.scored if self.scored else None

    @property
    def first_position_rate(self) -> float | None:
        return self.first_shown / self.judged if self.judged else None

    @property
    def flip_rate(self) -> float | None:
        return self.order_flips / self.agreement_pairs if self.agreement_pairs else None


def _shown_first(judgement: Judgement) -> Preference:
    return "A" if judgement.order == "as_is" else "B"


def score_model(
    model: str,
    results: Sequence[JudgeResult],
    gold: Mapping[str, Preference | None],
) -> ModelScore:
    """Reduce one model's results to a score, ignoring other models' results."""
    mine = [r for r in results if r.model == model]
    judgements = [r for r in mine if isinstance(r, Judgement)]
    failures = [r for r in mine if isinstance(r, JudgementFailure)]

    by_item: defaultdict[str, list[Judgement]] = defaultdict(list)
    for judgement in judgements:
        by_item[judgement.item_id].append(judgement)

    pairs = 0
    flips = 0
    for item_judgements in by_item.values():
        orders = {j.order: j for j in item_judgements}
        if len(orders) < 2:
            continue
        pairs += 1
        if len({j.preference for j in orders.values()}) > 1:
            flips += 1

    scored = [j for j in judgements if gold.get(j.item_id) is not None]

    return ModelScore(
        model=model,
        judged=len(judgements),
        failed=len(failures),
        chose_a=sum(1 for j in judgements if j.preference == "A"),
        chose_b=sum(1 for j in judgements if j.preference == "B"),
        first_shown=sum(1 for j in judgements if j.preference == _shown_first(j)),
        scored=len(scored),
        correct=sum(1 for j in scored if j.preference == gold[j.item_id]),
        agreement_pairs=pairs,
        order_flips=flips,
    )


def gold_map(items: Sequence[EvalItem]) -> dict[str, Preference | None]:
    """Index the gold preferences by item id."""
    return {item.item_id: item.gold_preference for item in items}


def score_all(
    models: Sequence[str],
    results: Sequence[JudgeResult],
    items: Sequence[EvalItem],
) -> list[ModelScore]:
    """Score every model, preserving the order the models were requested in."""
    gold = gold_map(items)
    return [score_model(model, results, gold) for model in models]
