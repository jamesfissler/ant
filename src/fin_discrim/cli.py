"""Command line entry point for the plan discrimination evaluation."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import anthropic
import click

from fin_discrim.items import EvalItem, load_items
from fin_discrim.judge import (
    Effort,
    JudgeResult,
    PresentationOrder,
    capabilities_for,
    judge_item,
    opposite,
)
from fin_discrim.report import render_report, results_to_json
from fin_discrim.scoring import score_all

DEFAULT_MODELS = ("claude-opus-5",)
DEFAULT_ITEMS_DIR = Path("data/eval_items")
EFFORT_LEVELS = ("low", "medium", "high", "xhigh", "max")
ORDERS = ("as_is", "swapped")


@dataclass(frozen=True, slots=True)
class RunConfig:
    """Everything a run needs, resolved from the command line."""

    items_dir: Path
    item_ids: tuple[str, ...] | None
    models: tuple[str, ...]
    order: PresentationOrder
    both_orders: bool
    effort: Effort
    max_tokens: int
    concurrency: int
    json_out: Path | None


def _unique(
    ctx: click.Context, param: click.Parameter, value: tuple[str, ...]
) -> tuple[str, ...]:
    """Reject a repeated value on a multiple-valued option."""
    del ctx
    if len(set(value)) != len(value):
        raise click.BadParameter("values must be unique", param=param)
    return value


def select_items(
    items: Sequence[EvalItem], wanted: Sequence[str] | None
) -> list[EvalItem]:
    """Filter to the requested item ids, erroring on ids that do not exist."""
    if wanted is None:
        return list(items)
    known = {item.item_id: item for item in items}
    missing = [item_id for item_id in wanted if item_id not in known]
    if missing:
        raise ValueError(
            f"unknown item id(s): {', '.join(missing)}; available: {', '.join(known)}"
        )
    return [known[item_id] for item_id in wanted]


def plan_run(
    items: Sequence[EvalItem], config: RunConfig
) -> list[tuple[str, EvalItem, PresentationOrder]]:
    """Enumerate the (model, item, order) calls a run will make."""
    orders: list[PresentationOrder] = (
        [config.order, opposite(config.order)] if config.both_orders else [config.order]
    )
    return [
        (model, item, order)
        for model in config.models
        for item in items
        for order in orders
    ]


def capability_notes(models: Sequence[str]) -> list[str]:
    """Warn about models whose requests will drop thinking and effort.

    Those models are judged under a different configuration to the rest of the
    run, which is a confound in any cross-model comparison, so say so up front.
    """
    return [
        f"note: {model} supports neither adaptive thinking nor effort; "
        f"it is judged without either, so its results are not directly "
        f"comparable with models that reason before answering."
        for model in models
        if not capabilities_for(model).adaptive_thinking
    ]


def run(
    client: anthropic.Anthropic, items: Sequence[EvalItem], config: RunConfig
) -> list[JudgeResult]:
    """Execute every judgement, in parallel, preserving deterministic order."""
    calls = plan_run(items, config)

    def judge(call: tuple[str, EvalItem, PresentationOrder]) -> JudgeResult:
        model, item, order = call
        return judge_item(
            client,
            model,
            item,
            order=order,
            effort=config.effort,
            max_tokens=config.max_tokens,
        )

    with ThreadPoolExecutor(max_workers=config.concurrency) as pool:
        return list(pool.map(judge, calls))


def execute(config: RunConfig) -> int:
    """Run the evaluation and print the report; returns the process exit code."""
    try:
        items = select_items(load_items(config.items_dir), config.item_ids)
    except ValueError as exc:
        click.echo(f"error: {exc}", err=True)
        return 2

    try:
        client = anthropic.Anthropic()
    except anthropic.AnthropicError as exc:
        click.echo(f"error: could not create an Anthropic client: {exc}", err=True)
        return 2

    calls = plan_run(items, config)
    click.echo(
        f"Judging {len(items)} item(s) with {len(config.models)} model(s) "
        f"-> {len(calls)} API call(s) at effort={config.effort}.",
        err=True,
    )
    for note in capability_notes(config.models):
        click.echo(note, err=True)

    results = run(client, items, config)
    scores = score_all(list(config.models), results, items)

    click.echo(render_report(items, results, scores))

    if config.json_out is not None:
        config.json_out.parent.mkdir(parents=True, exist_ok=True)
        config.json_out.write_text(
            results_to_json(items, results, scores), encoding="utf-8"
        )
        click.echo(f"Wrote full results to {config.json_out}", err=True)

    return 1 if any(score.failed for score in scores) else 0


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--model",
    "models",
    multiple=True,
    default=DEFAULT_MODELS,
    show_default=True,
    callback=_unique,
    metavar="MODEL",
    help="Claude model id to evaluate. Repeat to compare several models.",
)
@click.option(
    "--items-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=DEFAULT_ITEMS_DIR,
    show_default=True,
    help="Directory of eval item JSON files.",
)
@click.option(
    "--item",
    "item_ids",
    multiple=True,
    callback=_unique,
    metavar="ITEM_ID",
    help=(
        "Restrict the run to this item id (the JSON filename without .json). "
        "Repeat to select several. Defaults to every item in the directory."
    ),
)
@click.option(
    "--order",
    type=click.Choice(ORDERS),
    default="as_is",
    show_default=True,
    help="Whether plan A or plan B is shown first to the model.",
)
@click.option(
    "--both-orders",
    is_flag=True,
    help=(
        "Judge every item twice, once in each order, to measure position bias. "
        "Doubles the number of API calls."
    ),
)
@click.option(
    "--effort",
    type=click.Choice(EFFORT_LEVELS),
    default="high",
    show_default=True,
    help="Reasoning effort for the judging model.",
)
@click.option(
    "--max-tokens",
    type=click.IntRange(min=1),
    default=8000,
    show_default=True,
    help="Response cap per judgement.",
)
@click.option(
    "--concurrency",
    type=click.IntRange(min=1),
    default=4,
    show_default=True,
    help="Judgements to run in parallel.",
)
@click.option(
    "--json-out",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Optional path to write the full results, including each verdict's reasoning.",
)
def main(
    models: tuple[str, ...],
    items_dir: Path,
    item_ids: tuple[str, ...],
    order: str,
    both_orders: bool,
    effort: str,
    max_tokens: int,
    concurrency: int,
    json_out: Path | None,
) -> None:
    """Ask one or more Claude models which of two research plans is better.

    Each eval item pairs a seed research idea with two competing plans. Every
    model is asked to choose between them, and the answers are scored against
    the gold preferences. Gold preferences and gold critiques are never sent to
    the models.
    """
    config = RunConfig(
        items_dir=items_dir,
        item_ids=item_ids or None,
        models=models,
        order=cast(PresentationOrder, order),
        both_orders=both_orders,
        effort=cast(Effort, effort),
        max_tokens=max_tokens,
        concurrency=concurrency,
        json_out=json_out,
    )
    sys.exit(execute(config))


if __name__ == "__main__":
    main()
