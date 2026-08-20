"""Tests for eval item loading and gold preference parsing."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from fin_discrim.items import EvalItem, load_item, load_items, parse_preference


def write_item(directory: Path, name: str, **overrides: str) -> Path:
    payload = {
        "seed_idea": "an idea",
        "plan_A": "plan a body",
        "plan_B": "plan b body",
        "gold_preference": "",
        "gold_critique_A": "critique a",
        "gold_critique_B": "critique b",
        "why_B_is_convincing": "",
    }
    payload.update(overrides)
    path = directory / f"{name}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("A", "A"), ("b", "B"), ("Plan A", "A"), ("plan_b", "B"), ("", None), ("  ", None)],
)
def test_parse_preference_normalises(raw: str, expected: str | None) -> None:
    assert parse_preference(raw) == expected


def test_parse_preference_rejects_unknown_label() -> None:
    with pytest.raises(ValueError, match="unrecognised gold_preference"):
        parse_preference("neither")


def test_load_item_reads_all_fields(tmp_path: Path) -> None:
    path = write_item(tmp_path, "an-idea", gold_preference="A")
    item = load_item(path)
    assert item == EvalItem(
        item_id="an-idea",
        seed_idea="an idea",
        plan_a="plan a body",
        plan_b="plan b body",
        gold_preference="A",
    )
    assert item.is_labelled


def test_load_item_treats_blank_gold_as_unlabelled(tmp_path: Path) -> None:
    item = load_item(write_item(tmp_path, "unlabelled"))
    assert item.gold_preference is None
    assert not item.is_labelled


def test_load_item_rejects_missing_field(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"seed_idea": "x"}), encoding="utf-8")
    with pytest.raises(ValueError, match="missing required field 'plan_A'"):
        load_item(path)


def test_load_item_rejects_empty_plan(tmp_path: Path) -> None:
    path = write_item(tmp_path, "empty", plan_B="   ")
    with pytest.raises(ValueError, match="field 'plan_B' is empty"):
        load_item(path)


def test_load_items_sorts_and_requires_content(tmp_path: Path) -> None:
    write_item(tmp_path, "zebra")
    write_item(tmp_path, "alpha")
    assert [item.item_id for item in load_items(tmp_path)] == ["alpha", "zebra"]

    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(ValueError, match="no .json eval items"):
        load_items(empty)


def test_real_eval_items_load() -> None:
    """The checked-in eval items must stay loadable."""
    items = load_items(Path("data/eval_items"))
    assert items
    assert all(item.plan_a and item.plan_b and item.seed_idea for item in items)
