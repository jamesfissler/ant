"""Aggregating pointwise scores, and comparing them against expert scores.

Pure functions over results: nothing here calls a model or reads a file. When
an item carries no expert scores for a dimension the comparison fields are
``None`` rather than zero, so an unlabelled run reports model scores alone.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from statistics import fmean

from fin_discrim.items import EvalItem, Side
from fin_discrim.pointwise.assess import AssessResult, DimensionScore, ScoreFailure


@dataclass(frozen=True, slots=True)
class ScoredDimension:
    """One model score for one dimension, beside the expert score if there is one."""

    item_id: str
    side: Side
    dimension: str
    model_score: int
    expert_score: int | None

    @property
    def delta(self) -> int | None:
        """Model minus expert; ``None`` when no expert score was recorded."""
        if self.expert_score is None:
            return None
        return self.model_score - self.expert_score


@dataclass(frozen=True, slots=True)
class DimensionSummary:
    """One model's aggregate performance on one dimension."""

    model: str
    dimension: str
    scored: int
    mean_score: float
    failed: int
    compared: int
    """How many scores had an expert score to compare against."""
    mean_absolute_delta: float | None
    exact_matches: int | None

    @property
    def exact_match_rate(self) -> float | None:
        if not self.compared or self.exact_matches is None:
            return None
        return self.exact_matches / self.compared


def pair_with_expert(
    results: Sequence[AssessResult], items: Sequence[EvalItem]
) -> list[ScoredDimension]:
    """Attach each model score to the expert score for the same dimension."""
    by_id = {item.item_id: item for item in items}
    paired: list[ScoredDimension] = []
    for result in results:
        if not isinstance(result, DimensionScore):
            continue
        item = by_id.get(result.item_id)
        expert = (
            item.expert_scores(result.side).get(result.dimension)
            if item is not None
            else None
        )
        paired.append(
            ScoredDimension(
                item_id=result.item_id,
                side=result.side,
                dimension=result.dimension,
                model_score=result.score,
                expert_score=expert,
            )
        )
    return paired


def summarise(
    models: Sequence[str],
    dimensions: Sequence[str],
    results: Sequence[AssessResult],
    items: Sequence[EvalItem],
) -> list[DimensionSummary]:
    """One summary per (model, dimension), in the order given."""
    by_id = {item.item_id: item for item in items}
    summaries: list[DimensionSummary] = []
    for model in models:
        for dimension in dimensions:
            scored = [
                r
                for r in results
                if isinstance(r, DimensionScore)
                and r.model == model
                and r.dimension == dimension
            ]
            failed = sum(
                1
                for r in results
                if isinstance(r, ScoreFailure)
                and r.model == model
                and r.dimension == dimension
            )
            deltas: list[int] = []
            for result in scored:
                item = by_id.get(result.item_id)
                expert = (
                    item.expert_scores(result.side).get(result.dimension)
                    if item is not None
                    else None
                )
                if expert is not None:
                    deltas.append(result.score - expert)
            summaries.append(
                DimensionSummary(
                    model=model,
                    dimension=dimension,
                    scored=len(scored),
                    mean_score=fmean(r.score for r in scored) if scored else 0.0,
                    failed=failed,
                    compared=len(deltas),
                    mean_absolute_delta=(
                        fmean(abs(d) for d in deltas) if deltas else None
                    ),
                    exact_matches=sum(1 for d in deltas if d == 0) if deltas else None,
                )
            )
    return summaries
