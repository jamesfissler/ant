"""Tests for splitting plan documents and assembling eval items."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from fin_discrim.build_item import (
    build_item,
    main,
    parse_plan_document,
    parse_seed_ideas,
    render_item,
    select_seed_idea,
)
from fin_discrim.items import load_item

PLAN = """\
# A Title

## 1. The claim

The body of the plan.

---

## Critique of the Plan

### The question is not open

That part is weak.

---

## My Verdict

### Plan

The plan is confused about what it tests.

### Critique

The critique lands, mostly.
"""

SEEDS = """\
# Seed ideas

- First idea, all on one line.

- Second idea which wraps
  onto a continuation line.

- Third idea.
"""


def write(tmp_path: Path, name: str, text: str) -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_parse_seed_ideas_reads_bullets_and_joins_wrapped_lines() -> None:
    ideas = parse_seed_ideas(SEEDS)
    assert ideas == [
        "First idea, all on one line.",
        "Second idea which wraps onto a continuation line.",
        "Third idea.",
    ]


def test_parse_seed_ideas_ignores_prose_outside_bullets() -> None:
    assert parse_seed_ideas("# Title\n\nA paragraph.\n") == []


def test_select_seed_idea_is_one_based_and_range_checked() -> None:
    ideas = parse_seed_ideas(SEEDS)
    assert select_seed_idea(ideas, 1).startswith("First")
    assert select_seed_idea(ideas, 3) == "Third idea."
    for out_of_range in (0, 4):
        with pytest.raises(ValueError, match="out of range"):
            select_seed_idea(ideas, out_of_range)


def test_parse_plan_document_splits_the_four_sections() -> None:
    document = parse_plan_document(PLAN)
    assert document.plan.startswith("# A Title")
    assert document.plan.endswith("The body of the plan.")
    # The plan stops at the critique and carries no separator rule.
    assert "Critique of the Plan" not in document.plan
    assert "---" not in document.plan
    assert document.critique.startswith("### The question is not open")
    assert document.verdict_plan == "The plan is confused about what it tests."
    assert document.verdict_critique == "The critique lands, mostly."


def test_verdict_subsections_are_scoped_to_the_verdict() -> None:
    """`### Plan` headings inside the critique must not be picked up."""
    plan = PLAN.replace("### The question is not open", "### Plan")
    document = parse_plan_document(plan)
    assert document.verdict_plan == "The plan is confused about what it tests."


def test_headings_inside_code_fences_are_ignored() -> None:
    plan = PLAN.replace(
        "The body of the plan.",
        "```markdown\n## My Verdict\n### Plan\nnot a real section\n```",
    )
    document = parse_plan_document(plan)
    assert document.verdict_plan == "The plan is confused about what it tests."
    assert "not a real section" in document.plan


@pytest.mark.parametrize(
    ("broken", "message"),
    [
        (PLAN.replace("## Critique of the Plan", "## Something Else"), "no '## Critique"),
        (PLAN.replace("## My Verdict", "## Closing Thoughts"), "no '## My Verdict'"),
        (PLAN.replace("### Plan\n\nThe plan is confused", "### Notes\n\nThe plan is confused"), "no '### Plan'"),
        (PLAN + "\n## My Verdict\n\n### Plan\n\nx\n\n### Critique\n\ny\n", "appears 2 times"),
    ],
)
def test_parse_plan_document_rejects_a_malformed_document(broken: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        parse_plan_document(broken, "plan.md")


def test_parse_plan_document_rejects_an_empty_verdict_plan() -> None:
    plan = PLAN.replace("The plan is confused about what it tests.\n", "")
    with pytest.raises(ValueError, match="is empty"):
        parse_plan_document(plan, "plan.md")


def test_parse_plan_document_rejects_an_empty_critique() -> None:
    """The critique is an output field now, so a blank one cannot pass through."""
    plan = PLAN.replace("### The question is not open\n\nThat part is weak.\n", "")
    with pytest.raises(ValueError, match="Critique of the Plan' is empty"):
        parse_plan_document(plan, "plan.md")


def test_build_item_pairs_each_document_with_its_own_verdict() -> None:
    document_a = parse_plan_document(PLAN)
    document_b = parse_plan_document(PLAN.replace("A Title", "B Title"))
    item = build_item("  the seed idea  ", document_a, document_b)

    assert list(item) == [
        "seed_idea",
        "plan_A",
        "plan_B",
        "critique_A",
        "critique_B",
        "gold_preference",
        "gold_critique_A",
        "gold_critique_B",
        "why_alternative_is_convincing",
    ]
    assert item["seed_idea"] == "the seed idea"
    assert item["plan_A"].startswith("# A Title")
    assert item["plan_B"].startswith("# B Title")
    assert item["critique_A"] == document_a.critique
    assert item["critique_B"] == document_b.critique
    assert item["gold_critique_A"] == document_a.verdict_plan
    assert item["gold_critique_B"] == document_b.verdict_plan
    # The self-critique and the verdict on the plan are different sections.
    assert item["critique_A"] != item["gold_critique_A"]
    assert item["gold_preference"] == ""
    assert item["why_alternative_is_convincing"] == ""


def test_generated_item_loads_as_an_unlabelled_eval_item(tmp_path: Path) -> None:
    """The blank gold_preference must round-trip through the eval item loader."""
    document = parse_plan_document(PLAN)
    path = tmp_path / "an-idea.json"
    path.write_text(render_item(build_item("seed", document, document)), encoding="utf-8")

    item = load_item(path)
    assert item.item_id == "an-idea"
    assert item.gold_preference is None
    assert item.is_labelled is False


def test_cli_writes_the_item_for_the_requested_seed(tmp_path: Path) -> None:
    seeds = write(tmp_path, "seeds.md", SEEDS)
    plan_a = write(tmp_path, "a.md", PLAN)
    plan_b = write(tmp_path, "b.md", PLAN.replace("A Title", "B Title"))
    out = tmp_path / "nested" / "item.json"

    result = CliRunner().invoke(
        main,
        ["--seed-ideas", str(seeds), "--seed-index", "2",
         "--plan-a", str(plan_a), "--plan-b", str(plan_b), "--out", str(out)],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(out.read_text())
    assert payload["seed_idea"] == "Second idea which wraps onto a continuation line."
    assert payload["plan_B"].startswith("# B Title")


def test_cli_lists_seeds_with_one_based_indices(tmp_path: Path) -> None:
    seeds = write(tmp_path, "seeds.md", SEEDS)
    result = CliRunner().invoke(main, ["--seed-ideas", str(seeds), "--list-seeds"])
    assert result.exit_code == 0
    assert result.output.splitlines()[0] == "1\tFirst idea, all on one line."
    assert len(result.output.splitlines()) == 3


def test_cli_refuses_to_overwrite_without_force(tmp_path: Path) -> None:
    """A rebuild blanks gold_preference, so an existing item is protected."""
    seeds = write(tmp_path, "seeds.md", SEEDS)
    plan = write(tmp_path, "a.md", PLAN)
    out = write(tmp_path, "item.json", '{"gold_preference": "A"}')
    args = ["--seed-ideas", str(seeds), "--seed-index", "1",
            "--plan-a", str(plan), "--plan-b", str(plan), "--out", str(out)]

    result = CliRunner().invoke(main, args)
    assert result.exit_code == 1
    assert "already exists" in result.output
    assert json.loads(out.read_text())["gold_preference"] == "A"

    forced = CliRunner().invoke(main, [*args, "--force"])
    assert forced.exit_code == 0
    assert json.loads(out.read_text())["gold_preference"] == ""


def test_cli_requires_the_build_options_when_not_listing(tmp_path: Path) -> None:
    seeds = write(tmp_path, "seeds.md", SEEDS)
    result = CliRunner().invoke(main, ["--seed-ideas", str(seeds), "--seed-index", "1"])
    assert result.exit_code == 2
    assert "--plan-a" in result.output and "--out" in result.output


def test_cli_reports_a_malformed_plan_file(tmp_path: Path) -> None:
    seeds = write(tmp_path, "seeds.md", SEEDS)
    good = write(tmp_path, "a.md", PLAN)
    bad = write(tmp_path, "b.md", "# Just a title\n\nNo sections at all.\n")
    result = CliRunner().invoke(
        main,
        ["--seed-ideas", str(seeds), "--seed-index", "1", "--plan-a", str(good),
         "--plan-b", str(bad), "--out", str(tmp_path / "item.json")],
    )
    assert result.exit_code == 1
    assert "b.md" in result.output
    assert "Critique of the Plan" in result.output


def test_cli_reproduces_a_curated_eval_item(tmp_path: Path) -> None:
    """The real docs must still yield the checked-in item, byte for byte."""
    out = tmp_path / "order-book-imbalance.json"
    result = CliRunner().invoke(
        main,
        ["--seed-ideas", "docs/seed_ideas.md", "--seed-index", "1",
         "--plan-a", "docs/seed_idea_plans/order-book-imbalance.md",
         "--plan-b", "docs/evaluation_idea_plans/order-book-imbalance.md",
         "--out", str(out)],
    )
    assert result.exit_code == 0, result.output
    generated = json.loads(out.read_text())
    curated = json.loads(Path("data/eval_items/order-book-imbalance.json").read_text())
    for field in ("seed_idea", "plan_A", "plan_B", "gold_critique_A", "gold_critique_B"):
        assert generated[field] == curated[field], field
    # The critiques are new, so the curated item has nothing to compare against.
    assert generated["critique_A"].startswith("### ")
    assert "Critique of the Plan" not in generated["critique_A"]
