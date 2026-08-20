"""Tests for the pointwise assessment suite, driven by a stub client."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Self

import pytest
from anthropic import omit
from click.testing import CliRunner

from fin_discrim.items import EvalItem
from fin_discrim.pointwise import dimensions as registry
from fin_discrim.pointwise.assess import (
    DimensionScore,
    ScoreFailure,
    assess_dimension,
    build_prompt,
)
from fin_discrim.pointwise.cli import RunConfig, main, plan_run, run
from fin_discrim.pointwise.report import render_report, results_to_json
from fin_discrim.pointwise.scoring import pair_with_expert, summarise

PLAN_DIMENSION = registry.BY_KEY["falsifiability"]
CRITIQUE_DIMENSION = registry.BY_KEY["critique-bite"]


class StubStream:
    def __init__(self, message: object) -> None:
        self._message = message

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def get_final_message(self) -> object:
        return self._message


class StubMessages:
    def __init__(self, recorder: StubClient) -> None:
        self._recorder = recorder

    def stream(self, **kwargs: Any) -> StubStream:
        self._recorder.calls.append(kwargs)
        text = json.dumps(
            {"justification": "it says so", "score": self._recorder.score}
        )
        message = type(
            "Message",
            (),
            {
                "stop_reason": "end_turn",
                "stop_details": None,
                "content": [type("Block", (), {"type": "text", "text": text})()],
                "usage": type(
                    "Usage", (), {"input_tokens": 100, "output_tokens": 20}
                )(),
            },
        )()
        return StubStream(message)


class StubClient:
    """Records every request and returns a scripted score."""

    def __init__(self, score: int = 4) -> None:
        self.calls: list[dict[str, Any]] = []
        self.score = score
        self.messages = StubMessages(self)


def make_item(item_id: str = "one", **overrides: Any) -> EvalItem:
    base: dict[str, Any] = {
        "item_id": item_id,
        "seed_idea": f"seed for {item_id}",
        "plan_a": f"PLAN_A_BODY_{item_id}",
        "plan_b": f"PLAN_B_BODY_{item_id}",
        "gold_preference": "A",
        "critique_a": f"CRITIQUE_A_BODY_{item_id}",
        "critique_b": f"CRITIQUE_B_BODY_{item_id}",
    }
    base.update(overrides)
    return EvalItem(**base)


def make_config(**overrides: Any) -> RunConfig:
    base: dict[str, Any] = {
        "items_dir": Path("data/eval_items"),
        "item_ids": None,
        "models": ("claude-opus-5",),
        "dimensions": registry.DIMENSIONS,
        "side": "A",
        "both_sides": False,
        "effort": "high",
        "max_tokens": 8000,
        "concurrency": 2,
        "json_out": None,
    }
    base.update(overrides)
    return RunConfig(**base)


def test_registry_select_defaults_to_every_dimension() -> None:
    assert registry.select(None) == registry.DIMENSIONS
    assert registry.select(()) == registry.DIMENSIONS


def test_registry_select_keeps_registry_order() -> None:
    selected = registry.select(["critique-bite", "falsifiability"])
    assert [d.key for d in selected] == ["falsifiability", "critique-bite"]


def test_registry_select_rejects_an_unknown_dimension() -> None:
    with pytest.raises(ValueError, match="unknown dimension"):
        registry.select(["not-a-dimension"])


def test_every_dimension_has_a_unique_key_and_known_target() -> None:
    keys = [d.key for d in registry.DIMENSIONS]
    assert len(set(keys)) == len(keys)
    assert {d.target for d in registry.DIMENSIONS} <= {"plan", "critique"}


def test_plan_prompt_shows_the_plan_and_not_the_other_side() -> None:
    prompt = build_prompt(make_item(), "A", PLAN_DIMENSION)
    assert "PLAN_A_BODY_one" in prompt
    assert "PLAN_B_BODY_one" not in prompt
    # A plan is judged alone, so its own critique must not colour the score.
    assert "CRITIQUE_A_BODY_one" not in prompt
    assert PLAN_DIMENSION.question in prompt


def test_critique_prompt_includes_the_plan_it_criticises() -> None:
    prompt = build_prompt(make_item(), "B", CRITIQUE_DIMENSION)
    assert "CRITIQUE_B_BODY_one" in prompt
    assert "PLAN_B_BODY_one" in prompt
    assert "PLAN_A_BODY_one" not in prompt


def test_prompt_never_leaks_gold_or_expert_data() -> None:
    item = make_item(expert_scores_a={"falsifiability": 5})
    for dimension in registry.DIMENSIONS:
        prompt = build_prompt(item, "A", dimension)
        assert "gold" not in prompt.lower()
        assert "expert" not in prompt.lower()


def test_assess_dimension_returns_a_score() -> None:
    client = StubClient(score=5)
    result = assess_dimension(client, "claude-opus-5", make_item(), PLAN_DIMENSION)  # type: ignore[arg-type]
    assert isinstance(result, DimensionScore)
    assert result.score == 5
    assert result.dimension == "falsifiability"
    assert result.side == "A"
    assert client.calls[0]["thinking"] == {"type": "adaptive"}
    assert client.calls[0]["output_config"]["effort"] == "high"


def test_assess_dimension_adapts_to_a_legacy_model() -> None:
    """The capability table is shared with fin-discrim, not re-implemented."""
    client = StubClient()
    assess_dimension(client, "claude-haiku-4-5", make_item(), PLAN_DIMENSION)  # type: ignore[arg-type]
    assert client.calls[0]["thinking"] is omit
    assert "effort" not in client.calls[0]["output_config"]


def test_assess_dimension_fails_cleanly_when_the_critique_is_missing() -> None:
    """Items written before critiques existed must not silently score zero."""
    client = StubClient()
    item = make_item(critique_a="")
    result = assess_dimension(client, "claude-opus-5", item, CRITIQUE_DIMENSION)  # type: ignore[arg-type]
    assert isinstance(result, ScoreFailure)
    assert "no critique_A" in result.error
    assert not client.calls  # no API call was made


def test_plan_run_enumerates_model_item_side_dimension() -> None:
    items = [make_item("one"), make_item("two")]
    config = make_config(models=("m1", "m2"), both_sides=True)
    calls = plan_run(items, config)
    assert len(calls) == 2 * 2 * 2 * len(registry.DIMENSIONS)
    assert {side for _, _, side, _ in calls} == {"A", "B"}


def test_summarise_keeps_models_apart() -> None:
    """Two models scoring the same item must not share each other's numbers."""
    items = [make_item("one", expert_scores_a={"falsifiability": 3})]
    results = [
        DimensionScore("one", "m1", "A", "falsifiability", 3, "j", 1, 1),
        DimensionScore("one", "m2", "A", "falsifiability", 5, "j", 1, 1),
    ]
    first, second = summarise(["m1", "m2"], ["falsifiability"], results, items)
    assert (first.mean_score, first.mean_absolute_delta) == (3.0, 0.0)
    assert (second.mean_score, second.mean_absolute_delta) == (5.0, 2.0)
    assert first.exact_match_rate == 1.0
    assert second.exact_match_rate == 0.0


def test_summarise_reports_no_comparison_without_expert_scores() -> None:
    items = [make_item("one")]
    results = [DimensionScore("one", "m1", "A", "falsifiability", 4, "j", 1, 1)]
    (summary,) = summarise(["m1"], ["falsifiability"], results, items)
    assert summary.compared == 0
    assert summary.mean_absolute_delta is None
    assert summary.exact_match_rate is None


def test_summarise_counts_failures_separately() -> None:
    items = [make_item("one")]
    results = [ScoreFailure("one", "m1", "A", "falsifiability", "overloaded_error")]
    (summary,) = summarise(["m1"], ["falsifiability"], results, items)
    assert (summary.scored, summary.failed) == (0, 1)


def test_pair_with_expert_uses_the_side_being_assessed() -> None:
    item = make_item(
        "one",
        expert_scores_a={"falsifiability": 2},
        expert_scores_b={"falsifiability": 5},
    )
    results = [
        DimensionScore("one", "m1", "A", "falsifiability", 4, "j", 1, 1),
        DimensionScore("one", "m1", "B", "falsifiability", 4, "j", 1, 1),
    ]
    a, b = pair_with_expert(results, [item])
    assert (a.expert_score, a.delta) == (2, 2)
    assert (b.expert_score, b.delta) == (5, -1)


def test_report_renders_model_scores_without_expert_data() -> None:
    items = [make_item("one")]
    client = StubClient()
    config = make_config()
    results = run(client, items, config)  # type: ignore[arg-type]
    summaries = summarise(
        config.models, [d.key for d in config.dimensions], results, items
    )
    report = render_report(items, results, summaries)

    assert "POINTWISE PLAN ASSESSMENT" in report
    assert "falsifiability" in report and "critique-bite" in report
    assert "no item carries expert scores" in report
    # No expert column in the table itself when nothing was recorded.
    header = next(line for line in report.splitlines() if line.startswith("item  "))
    assert "expert" not in header and "delta" not in header


def test_report_shows_the_expert_comparison_when_present() -> None:
    items = [make_item("one", expert_scores_a={"falsifiability": 2})]
    client = StubClient(score=4)
    config = make_config(dimensions=registry.select(["falsifiability"]))
    results = run(client, items, config)  # type: ignore[arg-type]
    summaries = summarise(config.models, ["falsifiability"], results, items)
    report = render_report(items, results, summaries)

    header = next(line for line in report.splitlines() if line.startswith("item  "))
    assert "expert" in header and "delta" in header
    assert "+2" in report
    assert "no item carries expert scores" not in report


def test_results_to_json_carries_every_justification() -> None:
    items = [make_item("one")]
    client = StubClient()
    config = make_config()
    results = run(client, items, config)  # type: ignore[arg-type]
    summaries = summarise(
        config.models, [d.key for d in config.dimensions], results, items
    )
    payload = json.loads(results_to_json(results, summaries))
    assert len(payload["assessments"]) == len(registry.DIMENSIONS)
    assert all(a["justification"] == "it says so" for a in payload["assessments"])
    assert {a["outcome"] for a in payload["assessments"]} == {"scored"}


def test_cli_lists_dimensions() -> None:
    result = CliRunner().invoke(main, ["--list-dimensions"])
    assert result.exit_code == 0
    assert len(result.output.splitlines()) == len(registry.DIMENSIONS)
    assert "falsifiability\tplan\t" in result.output


def test_cli_rejects_an_unknown_dimension() -> None:
    result = CliRunner().invoke(main, ["--dimension", "nope"])
    assert result.exit_code == 2
    assert "unknown dimension" in result.output


def test_cli_rejects_duplicate_dimensions() -> None:
    result = CliRunner().invoke(
        main, ["--dimension", "kill-order", "--dimension", "kill-order"]
    )
    assert result.exit_code == 2
    assert "unique" in result.output


def test_cli_help_lists_the_options() -> None:
    result = CliRunner().invoke(main, ["--help"])
    assert result.exit_code == 0
    for option in ("--model", "--dimension", "--side", "--both-sides", "--json-out"):
        assert option in result.output


def test_real_eval_items_carry_the_critiques_the_suite_needs() -> None:
    """The checked-in items must support the critique dimensions."""
    from fin_discrim.items import load_items

    for item in load_items(Path("data/eval_items")):
        for side in ("A", "B"):
            assert item.critique(side).strip(), f"{item.item_id}/{side}"
