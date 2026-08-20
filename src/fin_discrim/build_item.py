"""Assembling one eval item from a seed idea and two plan documents.

A plan document holds four parts in a fixed order: the plan itself, a
``## Critique of the Plan`` section, then ``## My Verdict`` with ``### Plan``
and ``### Critique`` subsections. This module splits that structure apart and
recombines two such documents into the JSON shape :mod:`fin_discrim.items`
reads back, leaving the gold judgement fields blank for a human to fill in.

Deciding which two plan files belong to a given seed idea is the caller's job:
nothing here searches directories or guesses at a match.
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import click

CRITIQUE_HEADING = "Critique of the Plan"
VERDICT_HEADING = "My Verdict"
VERDICT_PLAN_HEADING = "Plan"
VERDICT_CRITIQUE_HEADING = "Critique"

_HEADING = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*$")
_FENCE = re.compile(r"^[ \t]*(```|~~~)")
_BULLET = re.compile(r"^[ \t]*[-*][ \t]+(.*)$")
_RULE = re.compile(r"^[ \t]*(?:-{3,}|\*{3,}|_{3,})[ \t]*$")


@dataclass(frozen=True, slots=True)
class PlanDocument:
    """The four sections of one plan markdown file, each already stripped."""

    plan: str
    """Everything before ``## Critique of the Plan``, including the title."""
    critique: str
    verdict_plan: str
    """The ``### Plan`` subsection of ``## My Verdict`` - the gold critique."""
    verdict_critique: str


@dataclass(frozen=True, slots=True)
class _Heading:
    level: int
    title: str
    line: int


def parse_seed_ideas(text: str) -> list[str]:
    """Every bullet in a seed ideas markdown file, in document order.

    A bullet may wrap over several lines; continuation lines are joined with a
    single space. Anything that is not part of a bullet is ignored, so a title
    or a stray paragraph does not become a seed idea.
    """
    ideas: list[str] = []
    current: list[str] | None = None

    def flush() -> None:
        nonlocal current
        if current is not None:
            joined = " ".join(part for part in current if part)
            if joined:
                ideas.append(joined)
        current = None

    for line in text.splitlines():
        bullet = _BULLET.match(line)
        if bullet is not None:
            flush()
            current = [bullet.group(1).strip()]
        elif not line.strip():
            flush()
        elif current is not None:
            current.append(line.strip())
    flush()
    return ideas


def select_seed_idea(ideas: Sequence[str], index: int) -> str:
    """Pick the 1-based ``index`` seed idea, erroring outside the range."""
    if not 1 <= index <= len(ideas):
        raise ValueError(
            f"seed index {index} is out of range; the file holds "
            f"{len(ideas)} seed idea(s)"
        )
    return ideas[index - 1]


def _headings(lines: Sequence[str]) -> list[_Heading]:
    """Every ATX heading, skipping fenced code blocks so that a ``## x`` line
    inside a snippet is not mistaken for a section."""
    found: list[_Heading] = []
    fence: str | None = None
    for number, line in enumerate(lines):
        marker = _FENCE.match(line)
        if marker is not None:
            token = marker.group(1)
            fence = token if fence is None else (None if token == fence else fence)
            continue
        if fence is not None:
            continue
        heading = _HEADING.match(line)
        if heading is not None:
            found.append(
                _Heading(len(heading.group(1)), heading.group(2).strip(), number)
            )
    return found


def _require(
    headings: Sequence[_Heading],
    level: int,
    title: str,
    source: str,
    within: str = "",
) -> _Heading:
    """The single heading with this level and title, or a ValueError saying so."""
    matches = [
        h
        for h in headings
        if h.level == level and h.title.casefold() == title.casefold()
    ]
    where = f" inside '{within}'" if within else ""
    if not matches:
        raise ValueError(f"{source}: no '{'#' * level} {title}' heading{where}")
    if len(matches) > 1:
        raise ValueError(
            f"{source}: '{'#' * level} {title}' appears {len(matches)} times"
            f"{where}; the section to extract is ambiguous"
        )
    return matches[0]


def _section_end(
    headings: Sequence[_Heading], start: _Heading, max_level: int, total: int
) -> int:
    """Where a section body stops: the next heading at or above ``max_level``."""
    return next(
        (h.line for h in headings if h.line > start.line and h.level <= max_level),
        total,
    )


def _body(lines: Sequence[str], start: int, stop: int) -> str:
    """A section's text, minus the blank lines and ``---`` separators the plan
    documents use between sections."""
    body = list(lines[start:stop])
    edge = lambda line: not line.strip() or _RULE.match(line) is not None
    while body and edge(body[0]):
        body.pop(0)
    while body and edge(body[-1]):
        body.pop()
    # Strip the block as a whole rather than per line: two trailing spaces
    # inside a paragraph are a markdown hard break and must survive.
    return "\n".join(body).strip()


def parse_plan_document(text: str, source: str = "<text>") -> PlanDocument:
    """Split one plan markdown file into its four sections.

    ``source`` only labels errors. Raises ValueError when a required heading is
    missing, duplicated, out of order, or heads an empty section.
    """
    lines = text.splitlines()
    headings = _headings(lines)
    total = len(lines)

    critique = _require(headings, 2, CRITIQUE_HEADING, source)
    verdict = _require(headings, 2, VERDICT_HEADING, source)
    if verdict.line < critique.line:
        raise ValueError(
            f"{source}: '## {VERDICT_HEADING}' appears before "
            f"'## {CRITIQUE_HEADING}'; the plan cannot be located"
        )

    verdict_end = _section_end(headings, verdict, 2, total)
    inner = [h for h in headings if verdict.line < h.line < verdict_end]
    within = f"## {VERDICT_HEADING}"
    verdict_plan = _require(inner, 3, VERDICT_PLAN_HEADING, source, within)
    verdict_critique = _require(inner, 3, VERDICT_CRITIQUE_HEADING, source, within)

    document = PlanDocument(
        plan=_body(lines, 0, critique.line),
        critique=_body(lines, critique.line + 1, verdict.line),
        verdict_plan=_body(
            lines,
            verdict_plan.line + 1,
            _section_end(headings, verdict_plan, 3, verdict_end),
        ),
        verdict_critique=_body(
            lines,
            verdict_critique.line + 1,
            _section_end(headings, verdict_critique, 3, verdict_end),
        ),
    )

    if not document.plan:
        raise ValueError(f"{source}: the plan section is empty")
    if not document.verdict_plan:
        raise ValueError(
            f"{source}: '### {VERDICT_PLAN_HEADING}' under "
            f"'## {VERDICT_HEADING}' is empty"
        )
    return document


def build_item(
    seed_idea: str, plan_a: PlanDocument, plan_b: PlanDocument
) -> dict[str, str]:
    """The eval item payload; gold preference and rationale are left blank."""
    idea = seed_idea.strip()
    if not idea:
        raise ValueError("seed idea is empty")
    return {
        "seed_idea": idea,
        "plan_A": plan_a.plan,
        "plan_B": plan_b.plan,
        "gold_preference": "",
        "gold_critique_A": plan_a.verdict_plan,
        "gold_critique_B": plan_b.verdict_plan,
        "why_alternative_is_convincing": "",
    }


def render_item(item: dict[str, str]) -> str:
    """Serialise an item the way the checked-in eval items are formatted."""
    return json.dumps(item, indent=2, ensure_ascii=False) + "\n"


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise click.ClickException(f"could not read {path}: {exc}") from exc


def _plan(path: Path) -> PlanDocument:
    try:
        return parse_plan_document(_read(path), str(path))
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--seed-ideas",
    "seed_ideas_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Markdown file whose bullets are the seed research ideas.",
)
@click.option(
    "--seed-index",
    type=click.IntRange(min=1),
    default=None,
    metavar="N",
    help="Which seed idea to build, 1-based, as listed by --list-seeds.",
)
@click.option(
    "--plan-a",
    "plan_a_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Plan markdown file for this idea, becoming plan_A and gold_critique_A.",
)
@click.option(
    "--plan-b",
    "plan_b_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Plan markdown file for this idea, becoming plan_B and gold_critique_B.",
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Where to write the item JSON. Parent directories are created.",
)
@click.option(
    "--force",
    is_flag=True,
    help=(
        "Overwrite --out if it already exists. Off by default: a generated item "
        "blanks gold_preference, so a rebuild would discard hand-filled labels."
    ),
)
@click.option(
    "--list-seeds",
    is_flag=True,
    help="Print each seed idea with its index and exit, for a driver to match on.",
)
def main(
    seed_ideas_path: Path,
    seed_index: int | None,
    plan_a_path: Path | None,
    plan_b_path: Path | None,
    out_path: Path | None,
    force: bool,
    list_seeds: bool,
) -> None:
    """Build one eval item JSON from a seed idea and its two plan documents.

    The caller decides which plan files belong to the seed idea; this command
    only extracts and combines them. gold_preference and
    why_alternative_is_convincing are written blank, for a human to fill in.
    """
    ideas = parse_seed_ideas(_read(seed_ideas_path))
    if not ideas:
        raise click.ClickException(f"{seed_ideas_path}: contains no bullet seed ideas")

    if list_seeds:
        for number, idea in enumerate(ideas, start=1):
            click.echo(f"{number}\t{idea}")
        return

    if (
        seed_index is None
        or plan_a_path is None
        or plan_b_path is None
        or out_path is None
    ):
        missing = [
            name
            for name, value in (
                ("--seed-index", seed_index),
                ("--plan-a", plan_a_path),
                ("--plan-b", plan_b_path),
                ("--out", out_path),
            )
            if value is None
        ]
        raise click.UsageError(
            f"missing required option(s): {', '.join(missing)} "
            f"(or pass --list-seeds to enumerate the seed ideas)"
        )

    if out_path.exists() and not force:
        raise click.ClickException(
            f"{out_path} already exists; pass --force to overwrite it "
            f"(any gold_preference recorded there will be blanked)"
        )

    try:
        seed_idea = select_seed_idea(ideas, seed_index)
    except ValueError as exc:
        raise click.ClickException(f"{seed_ideas_path}: {exc}") from exc

    try:
        item = build_item(seed_idea, _plan(plan_a_path), _plan(plan_b_path))
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_item(item), encoding="utf-8")
    click.echo(
        f"Wrote {out_path} for seed idea {seed_index}: {seed_idea[:60]}...",
        err=True,
    )


if __name__ == "__main__":
    main()
