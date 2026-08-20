"""Rendering pointwise assessments as text and as a machine-readable dump."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import asdict
from typing import Any

from fin_discrim.items import EvalItem
from fin_discrim.pointwise.assess import AssessResult, DimensionScore, ScoreFailure
from fin_discrim.pointwise.scoring import (
    DimensionSummary,
    ScoredDimension,
    pair_with_expert,
)
from fin_discrim.report import format_table


def _signed(value: int | None) -> str:
    return "  -" if value is None else f"{value:+3d}"


def _mean(value: float | None) -> str:
    return "  n/a" if value is None else f"{value:5.2f}"


def render_report(
    items: Sequence[EvalItem],
    results: Sequence[AssessResult],
    summaries: Sequence[DimensionSummary],
) -> str:
    """Per-submission scores, then per-model means and expert agreement."""
    models = list(dict.fromkeys(s.model for s in summaries))
    dimensions = list(dict.fromkeys(s.dimension for s in summaries))
    compared = any(s.compared for s in summaries)

    lines: list[str] = ["", "=" * 78, "POINTWISE PLAN ASSESSMENT", "=" * 78, ""]
    lines.append(
        f"{len(items)} item(s), {len(models)} model(s), "
        f"{len(dimensions)} dimension(s), {len(results)} assessment(s)."
    )
    lines.append("")

    scores: dict[tuple[str, str, str, str], ScoredDimension] = {}
    for result, paired in zip(
        [r for r in results if isinstance(r, DimensionScore)],
        pair_with_expert(results, items),
    ):
        scores[(result.model, result.item_id, result.side, result.dimension)] = paired

    header = "Scores by submission  (1-5; expert column shown where recorded)"
    lines.append(header)
    lines.append("")
    headers = ["item", "side", "dimension", *models]
    if compared:
        headers += ["expert", *(f"{m} delta" for m in models)]
    rows: list[list[str]] = []
    for item in items:
        for side in ("A", "B"):
            for dimension in dimensions:
                keys = [(m, item.item_id, side, dimension) for m in models]
                found = [scores.get(key) for key in keys]
                if not any(found):
                    continue
                row = [item.item_id, side, dimension]
                row += ["err" if s is None else str(s.model_score) for s in found]
                if compared:
                    expert = next(
                        (s.expert_score for s in found if s is not None), None
                    )
                    row.append("-" if expert is None else str(expert))
                    row += [_signed(None if s is None else s.delta) for s in found]
                rows.append(row)
    lines += format_table(headers, rows)
    lines.append("")

    lines.append("Per-model means")
    lines.append("")
    summary_headers = ["model", "dimension", "scored", "mean", "errors"]
    if compared:
        summary_headers += ["compared", "mean |delta|", "exact"]
    summary_rows: list[list[str]] = []
    for summary in summaries:
        row = [
            summary.model,
            summary.dimension,
            str(summary.scored),
            f"{summary.mean_score:4.2f}" if summary.scored else " n/a",
            str(summary.failed),
        ]
        if compared:
            rate = summary.exact_match_rate
            row += [
                str(summary.compared),
                _mean(summary.mean_absolute_delta),
                "  n/a" if rate is None else f"{rate:6.1%}",
            ]
        summary_rows.append(row)
    lines += format_table(summary_headers, summary_rows)
    lines.append("")

    if not compared:
        lines.append(
            "NOTE: no item carries expert scores, so these are model scores "
            "only. Add an 'expert_scores_A'/'expert_scores_B' object to an item "
            "to have the report compare against it."
        )
        lines.append("")

    failures = [r for r in results if isinstance(r, ScoreFailure)]
    if failures:
        lines.append("Failures")
        lines.append("")
        for failure in failures:
            lines.append(
                f"  {failure.model} / {failure.item_id} / {failure.side} / "
                f"{failure.dimension}: {failure.error}"
            )
        lines.append("")

    return "\n".join(lines)


def results_to_json(
    results: Sequence[AssessResult], summaries: Sequence[DimensionSummary]
) -> str:
    """Serialise the run, including each score's justification, for inspection."""
    payload: dict[str, Any] = {
        "summaries": [
            {**asdict(summary), "exact_match_rate": summary.exact_match_rate}
            for summary in summaries
        ],
        "assessments": [
            {
                **asdict(result),
                "outcome": "error" if isinstance(result, ScoreFailure) else "scored",
            }
            for result in results
        ],
    }
    return json.dumps(payload, indent=2) + "\n"
