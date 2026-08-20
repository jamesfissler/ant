"""Rendering run results as a human-readable report and a machine-readable dump."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import asdict
from typing import Any

from fin_discrim.items import EvalItem
from fin_discrim.judge import Judgement, JudgementFailure, JudgeResult
from fin_discrim.scoring import ModelScore, gold_map


def _pct(value: float | None) -> str:
    return "  n/a" if value is None else f"{value:6.1%}"


def _table(headers: list[str], rows: list[list[str]]) -> list[str]:
    widths = [
        max(len(headers[i]), *(len(row[i]) for row in rows)) if rows else len(headers[i])
        for i in range(len(headers))
    ]
    fmt = lambda cells: "  ".join(c.ljust(w) for c, w in zip(cells, widths)).rstrip()
    return [fmt(headers), fmt(["-" * w for w in widths]), *(fmt(r) for r in rows)]


def render_report(
    items: Sequence[EvalItem],
    results: Sequence[JudgeResult],
    scores: Sequence[ModelScore],
) -> str:
    """Build the full text report: per-item grid, per-model scores, and failures."""
    gold = gold_map(items)
    labelled = sum(1 for value in gold.values() if value is not None)
    models = [score.model for score in scores]
    lines: list[str] = ["", "=" * 78, "PLAN DISCRIMINATION REPORT", "=" * 78, ""]
    lines.append(
        f"{len(items)} items ({labelled} with a gold preference), "
        f"{len(models)} model(s), {len(results)} judgement(s)."
    )
    lines.append("")

    verdicts: dict[tuple[str, str], list[Judgement]] = {}
    for result in results:
        if isinstance(result, Judgement):
            verdicts.setdefault((result.item_id, result.model), []).append(result)

    lines.append("Per-item verdicts  (gold | model choice, ! marks a miss)")
    lines.append("")
    rows: list[list[str]] = []
    for item in items:
        row = [item.item_id, item.gold_preference or "-"]
        for model in models:
            found = verdicts.get((item.item_id, model), [])
            if not found:
                row.append("err")
                continue
            cells: list[str] = []
            for judgement in sorted(found, key=lambda j: j.order):
                mark = ""
                if item.gold_preference is not None:
                    mark = "" if judgement.preference == item.gold_preference else "!"
                suffix = "" if len(found) == 1 else f"/{judgement.order}"
                cells.append(f"{judgement.preference}{mark}{suffix}")
            row.append(" ".join(cells))
        rows.append(row)
    lines += _table(["item", "gold", *models], rows)
    lines.append("")

    lines.append("Per-model scores")
    lines.append("")
    score_rows = [
        [
            score.model,
            f"{score.correct}/{score.scored}",
            _pct(score.accuracy),
            f"{score.chose_a}/{score.chose_b}",
            _pct(score.first_position_rate),
            "n/a" if score.flip_rate is None else f"{score.order_flips}/{score.agreement_pairs}",
            str(score.failed),
        ]
        for score in scores
    ]
    lines += _table(
        ["model", "correct", "accuracy", "A/B", "picked 1st", "flips", "errors"],
        score_rows,
    )
    lines.append("")

    if labelled == 0:
        lines.append(
            "NOTE: no item carries a gold_preference, so accuracy is undefined. "
            "Fill in the gold_preference fields to score the models."
        )
        lines.append("")
    if any(score.agreement_pairs for score in scores):
        lines.append(
            "'flips' counts items where a model changed its answer when the two "
            "plans swapped places; a high rate means the verdicts track position, "
            "not quality."
        )
        lines.append("")
    elif len({r.order for r in results}) == 1:
        lines.append(
            "NOTE: every item was judged in one presentation order only, so "
            "position bias is unmeasured. Re-run with --both-orders to control "
            "for it."
        )
        lines.append("")

    failures = [r for r in results if isinstance(r, JudgementFailure)]
    if failures:
        lines.append("Failures")
        lines.append("")
        for failure in failures:
            lines.append(
                f"  {failure.model} / {failure.item_id} / {failure.order}: {failure.error}"
            )
        lines.append("")

    return "\n".join(lines)


def results_to_json(
    items: Sequence[EvalItem],
    results: Sequence[JudgeResult],
    scores: Sequence[ModelScore],
) -> str:
    """Serialise the run, including each judge's reasoning, for later inspection."""
    gold = gold_map(items)
    payload: dict[str, Any] = {
        "items": [
            {"item_id": item.item_id, "gold_preference": item.gold_preference}
            for item in items
        ],
        "scores": [
            {
                **asdict(score),
                "accuracy": score.accuracy,
                "first_position_rate": score.first_position_rate,
                "flip_rate": score.flip_rate,
            }
            for score in scores
        ],
        "judgements": [
            {
                **asdict(result),
                "outcome": (
                    "error"
                    if isinstance(result, JudgementFailure)
                    else (
                        "unscored"
                        if gold[result.item_id] is None
                        else (
                            "correct"
                            if result.preference == gold[result.item_id]
                            else "incorrect"
                        )
                    )
                ),
            }
            for result in results
        ],
    }
    return json.dumps(payload, indent=2) + "\n"
