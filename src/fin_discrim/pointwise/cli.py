"""Command line entry point for the pointwise plan assessment suite."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import anthropic
import click

from fin_discrim.cli import (
    DEFAULT_ITEMS_DIR,
    EFFORT_LEVELS,
    capability_notes,
    select_items,
)
from fin_discrim.items import EvalItem, Side, load_items
from fin_discrim.judge import Effort
from fin_discrim.pointwise import dimensions as registry
from fin_discrim.pointwise.assess import AssessResult, assess_dimension
from fin_discrim.pointwise.dimensions import Dimension
from fin_discrim.pointwise.report import render_report, results_to_json
from fin_discrim.pointwise.scoring import summarise

DEFAULT_MODELS = ("claude-opus-5",)
SIDES = ("A", "B")


@dataclass(frozen=True, slots=True)
class RunConfig:
    """Everything a pointwise run needs, resolved from the command line."""

    items_dir: Path
    item_ids: tuple[str, ...] | None
    models: tuple[str, ...]
    dimensions: tuple[Dimension, ...]
    side: Side
    both_sides: bool
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


def plan_run(
    items: Sequence[EvalItem], config: RunConfig
) -> list[tuple[str, EvalItem, Side, Dimension]]:
    """Enumerate the (model, item, side, dimension) calls a run will make."""
    sides: list[Side] = list(SIDES) if config.both_sides else [config.side]
    return [
        (model, item, side, dimension)
        for model in config.models
        for item in items
        for side in sides
        for dimension in config.dimensions
    ]


def run(
    client: anthropic.Anthropic, items: Sequence[EvalItem], config: RunConfig
) -> list[AssessResult]:
    """Execute every assessment, in parallel, preserving deterministic order."""
    calls = plan_run(items, config)

    def assess(call: tuple[str, EvalItem, Side, Dimension]) -> AssessResult:
        model, item, side, dimension = call
        return assess_dimension(
            client,
            model,
            item,
            dimension,
            side=side,
            effort=config.effort,
            max_tokens=config.max_tokens,
        )

    with ThreadPoolExecutor(max_workers=config.concurrency) as pool:
        return list(pool.map(assess, calls))


def execute(config: RunConfig) -> int:
    """Run the assessment and print the report; returns the process exit code."""
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
        f"Assessing {len(items)} item(s) on {len(config.dimensions)} dimension(s) "
        f"with {len(config.models)} model(s) -> {len(calls)} API call(s) "
        f"at effort={config.effort}.",
        err=True,
    )
    for note in capability_notes(config.models):
        click.echo(note, err=True)

    results = run(client, items, config)
    summaries = summarise(
        config.models, [d.key for d in config.dimensions], results, items
    )
    click.echo(render_report(items, results, summaries))

    if config.json_out is not None:
        config.json_out.parent.mkdir(parents=True, exist_ok=True)
        config.json_out.write_text(
            results_to_json(results, summaries), encoding="utf-8"
        )
        click.echo(f"Wrote full results to {config.json_out}", err=True)

    return 1 if any(summary.failed for summary in summaries) else 0


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--model",
    "models",
    multiple=True,
    default=DEFAULT_MODELS,
    show_default=True,
    callback=_unique,
    metavar="MODEL",
    help="Claude model id to assess with. Repeat to compare several models.",
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
    "--dimension",
    "dimension_keys",
    multiple=True,
    callback=_unique,
    metavar="KEY",
    help=(
        "Restrict the run to this dimension. Repeat to select several. "
        "Defaults to every dimension; --list-dimensions shows them."
    ),
)
@click.option(
    "--side",
    type=click.Choice(SIDES),
    default="A",
    show_default=True,
    help="Which of the item's two submissions to assess.",
)
@click.option(
    "--both-sides",
    is_flag=True,
    help="Assess both submissions of every item. Doubles the number of API calls.",
)
@click.option(
    "--effort",
    type=click.Choice(EFFORT_LEVELS),
    default="high",
    show_default=True,
    help="Reasoning effort for the assessing model.",
)
@click.option(
    "--max-tokens",
    type=click.IntRange(min=1),
    default=8000,
    show_default=True,
    help="Response cap per assessment.",
)
@click.option(
    "--concurrency",
    type=click.IntRange(min=1),
    default=4,
    show_default=True,
    help="Assessments to run in parallel.",
)
@click.option(
    "--json-out",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Optional path to write the full results, including each justification.",
)
@click.option(
    "--list-dimensions",
    is_flag=True,
    help="Print the available dimensions and exit.",
)
def main(
    models: tuple[str, ...],
    items_dir: Path,
    item_ids: tuple[str, ...],
    dimension_keys: tuple[str, ...],
    side: str,
    both_sides: bool,
    effort: str,
    max_tokens: int,
    concurrency: int,
    json_out: Path | None,
    list_dimensions: bool,
) -> None:
    """Score one side of each eval item on a suite of quality dimensions.

    Where fin-discrim compares an item's two plans against each other, this
    scores a single plan and its critique on their own terms, one model call
    per dimension. Dimensions live in fin_discrim.pointwise.dimensions and are
    meant to be added to.
    """
    if list_dimensions:
        for dimension in registry.DIMENSIONS:
            click.echo(f"{dimension.key}\t{dimension.target}\t{dimension.question}")
        return

    try:
        selected = registry.select(dimension_keys)
    except ValueError as exc:
        raise click.BadParameter(str(exc), param_hint="--dimension") from exc

    config = RunConfig(
        items_dir=items_dir,
        item_ids=item_ids or None,
        models=models,
        dimensions=selected,
        side=cast(Side, side),
        both_sides=both_sides,
        effort=cast(Effort, effort),
        max_tokens=max_tokens,
        concurrency=concurrency,
        json_out=json_out,
    )
    sys.exit(execute(config))


if __name__ == "__main__":
    main()
