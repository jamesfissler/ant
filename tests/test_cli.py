"""End-to-end tests driving the run loop with a stub Anthropic client."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any, Self

import pytest
from click.testing import CliRunner, Result

from fin_discrim.cli import RunConfig, main, plan_run, run, select_items
from fin_discrim.items import EvalItem, load_items
from fin_discrim.judge import Judgement, JudgementFailure
from fin_discrim.report import render_report, results_to_json
from fin_discrim.scoring import score_all


class StubStream:
    """Stands in for the SDK's streaming context manager."""

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
        choice = self._recorder.choose(kwargs)
        text = json.dumps(
            {
                "reasoning": "it tests the claim",
                "preferred_plan": choice,
                "confidence": "high",
            }
        )
        message = type(
            "Message",
            (),
            {
                "stop_reason": "end_turn",
                "stop_details": None,
                "content": [type("Block", (), {"type": "text", "text": text})()],
                "usage": type("Usage", (), {"input_tokens": 100, "output_tokens": 20})(),
            },
        )()
        return StubStream(message)


class StubClient:
    """Records every request and returns a scripted verdict."""

    def __init__(self, always: str = "Plan 1") -> None:
        self.calls: list[dict[str, Any]] = []
        self._always = always
        self.messages = StubMessages(self)

    def choose(self, kwargs: dict[str, Any]) -> str:
        return self._always


def make_item(item_id: str, gold: str | None = "A") -> EvalItem:
    return EvalItem(
        item_id=item_id,
        seed_idea=f"seed for {item_id}",
        plan_a=f"PLAN_A_BODY_{item_id}",
        plan_b=f"PLAN_B_BODY_{item_id}",
        gold_preference=gold,  # type: ignore[arg-type]
    )


def make_config(**overrides: Any) -> RunConfig:
    base: dict[str, Any] = {
        "items_dir": Path("data/eval_items"),
        "item_ids": None,
        "models": ("model-x",),
        "order": "as_is",
        "both_orders": False,
        "effort": "high",
        "max_tokens": 8000,
        "concurrency": 2,
        "json_out": None,
    }
    base.update(overrides)
    return RunConfig(**base)


def test_plan_run_enumerates_model_item_order_triples() -> None:
    items = [make_item("one"), make_item("two")]
    config = make_config(models=("m1", "m2"), both_orders=True)
    calls = plan_run(items, config)
    assert len(calls) == 8
    assert {order for _, _, order in calls} == {"as_is", "swapped"}


def test_run_maps_first_position_choice_back_to_the_right_label() -> None:
    items = [make_item("one")]
    client = StubClient(always="Plan 1")

    as_is = run(client, items, make_config())  # type: ignore[arg-type]
    assert isinstance(as_is[0], Judgement)
    assert as_is[0].preference == "A"

    swapped = run(client, items, make_config(order="swapped"))  # type: ignore[arg-type]
    assert isinstance(swapped[0], Judgement)
    assert swapped[0].preference == "B"


def test_run_never_sends_gold_data_to_the_model() -> None:
    """Gold preferences and critiques stay client-side."""
    items = load_items(Path("data/eval_items"))
    client = StubClient()
    run(client, items, make_config(both_orders=True))  # type: ignore[arg-type]

    assert client.calls
    for call, item in zip(client.calls, items * 2):
        sent = json.dumps(
            {"system": call["system"], "messages": call["messages"]}
        ).lower()
        assert "gold" not in sent
        if item.gold_preference is not None:
            assert "gold_preference" not in sent


def test_run_sends_both_plans_and_the_seed_idea() -> None:
    items = [make_item("one")]
    client = StubClient()
    run(client, items, make_config())  # type: ignore[arg-type]
    content = client.calls[0]["messages"][0]["content"]
    assert "PLAN_A_BODY_one" in content
    assert "PLAN_B_BODY_one" in content
    assert "seed for one" in content


def test_run_passes_effort_and_schema_through() -> None:
    client = StubClient()
    run(client, [make_item("one")], make_config(effort="low"))  # type: ignore[arg-type]
    output_config = client.calls[0]["output_config"]
    assert output_config["effort"] == "low"
    assert output_config["format"]["type"] == "json_schema"


def test_report_renders_for_a_full_run(tmp_path: Path) -> None:
    items = [make_item("one"), make_item("two", gold=None)]
    client = StubClient()
    config = make_config(models=("model-x",), both_orders=True)
    results = run(client, items, config)  # type: ignore[arg-type]
    scores = score_all(list(config.models), results, items)

    report = render_report(items, results, scores)
    assert "PLAN DISCRIMINATION REPORT" in report
    assert "model-x" in report
    assert "one" in report and "two" in report
    # A stub that always picks the first plan is maximally position-biased.
    assert scores[0].flip_rate == 1.0

    payload = json.loads(results_to_json(items, results, scores))
    assert len(payload["judgements"]) == 4
    assert {j["outcome"] for j in payload["judgements"]} == {
        "correct",
        "incorrect",
        "unscored",
    }


def test_report_notes_when_no_gold_labels_exist() -> None:
    items = [make_item("one", gold=None)]
    client = StubClient()
    results = run(client, items, make_config())  # type: ignore[arg-type]
    scores = score_all(["model-x"], results, items)
    assert "no item carries a gold_preference" in render_report(items, results, scores)


def test_failed_judgement_is_reported_not_raised() -> None:
    items = [make_item("one")]
    results = [JudgementFailure("one", "model-x", "as_is", "overloaded_error")]
    scores = score_all(["model-x"], list(results), items)
    report = render_report(items, results, scores)
    assert "Failures" in report
    assert "overloaded_error" in report
    assert scores[0].failed == 1


def test_select_items_filters_and_rejects_unknown_ids() -> None:
    items = [make_item("one"), make_item("two")]
    assert [i.item_id for i in select_items(items, ["two"])] == ["two"]
    with pytest.raises(ValueError, match="unknown item id"):
        select_items(items, ["nope"])


class RecordingExecute:
    """Captures the RunConfig the command builds, without calling the API."""

    def __init__(self, exit_code: int = 0) -> None:
        self.config: RunConfig | None = None
        self._exit_code = exit_code

    def __call__(self, config: RunConfig) -> int:
        self.config = config
        return self._exit_code


@pytest.fixture
def invoke(
    monkeypatch: pytest.MonkeyPatch,
) -> Callable[..., tuple[Result, RecordingExecute]]:
    """Run the click command with `execute` stubbed out, so no API call happens."""
    from fin_discrim import cli as cli_module

    def _invoke(*args: str, exit_code: int = 0) -> tuple[Result, RecordingExecute]:
        recorder = RecordingExecute(exit_code)
        monkeypatch.setattr(cli_module, "execute", recorder)
        result = CliRunner().invoke(cli_module.main, list(args))
        return result, recorder

    return _invoke


def test_cli_help_lists_the_options() -> None:
    result = CliRunner().invoke(main, ["--help"])
    assert result.exit_code == 0
    for option in ("--model", "--items-dir", "--both-orders", "--effort", "--json-out"):
        assert option in result.output


def test_cli_defaults_resolve_to_a_run_config(
    invoke: Callable[..., tuple[Result, RecordingExecute]],
) -> None:
    result, recorder = invoke()
    assert result.exit_code == 0
    config = recorder.config
    assert config is not None
    assert config.models == ("claude-opus-5",)
    assert config.item_ids is None
    assert config.order == "as_is"
    assert config.both_orders is False
    assert config.effort == "high"


def test_cli_repeated_model_and_item_options_accumulate(
    invoke: Callable[..., tuple[Result, RecordingExecute]],
) -> None:
    result, recorder = invoke(
        "--model", "claude-opus-5",
        "--model", "claude-sonnet-5",
        "--item", "sector-mean-reversion",
        "--both-orders",
        "--effort", "max",
    )
    assert result.exit_code == 0
    config = recorder.config
    assert config is not None
    assert config.models == ("claude-opus-5", "claude-sonnet-5")
    assert config.item_ids == ("sector-mean-reversion",)
    assert config.both_orders is True
    assert config.effort == "max"


def test_cli_rejects_duplicate_models(
    invoke: Callable[..., tuple[Result, RecordingExecute]],
) -> None:
    result, recorder = invoke("--model", "claude-opus-5", "--model", "claude-opus-5")
    assert result.exit_code == 2
    assert "unique" in result.output
    assert recorder.config is None


def test_cli_rejects_unknown_effort(
    invoke: Callable[..., tuple[Result, RecordingExecute]],
) -> None:
    result, _ = invoke("--effort", "turbo")
    assert result.exit_code == 2
    assert "turbo" in result.output


def test_cli_rejects_non_positive_concurrency(
    invoke: Callable[..., tuple[Result, RecordingExecute]],
) -> None:
    result, _ = invoke("--concurrency", "0")
    assert result.exit_code == 2


def test_cli_rejects_missing_items_dir(
    invoke: Callable[..., tuple[Result, RecordingExecute]],
) -> None:
    result, _ = invoke("--items-dir", "does/not/exist")
    assert result.exit_code == 2
    assert "does not exist" in result.output


def test_cli_propagates_the_execute_exit_code(
    invoke: Callable[..., tuple[Result, RecordingExecute]],
) -> None:
    result, _ = invoke(exit_code=1)
    assert result.exit_code == 1
