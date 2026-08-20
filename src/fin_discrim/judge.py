"""Asking a Claude model which of two research plans is better.

The gold preference and gold critiques are never referenced here: a judge sees
only the seed idea and the two plans, presented under neutral labels.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal, cast

import anthropic
from anthropic import Omit, omit
from anthropic.types import MessageParam, OutputConfigParam, ThinkingConfigParam
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from fin_discrim.items import EvalItem, Preference

PresentationOrder = Literal["as_is", "swapped"]
Confidence = Literal["low", "medium", "high"]
Effort = Literal["low", "medium", "high", "xhigh", "max"]

SYSTEM_PROMPT = """\
You are a senior research director at a systematic investment manager. Two \
independent researchers have each written a plan for investigating the same \
seed research idea. You must decide which plan you would fund.

Judge the plans on how well they would establish whether the idea is real and \
tradeable:

- Does the plan test the actual claim, or does it assume the answer and move \
  straight to implementation?
- Does it identify the confounds that would make a positive result spurious, \
  and does it design tests that isolate them?
- Does it order the work so that the cheapest tests that could kill the idea \
  run first?
- Are the success criteria pre-registered and defensible, or are the thresholds \
  arbitrary numbers that could be moved after seeing results?
- Does it engage honestly with frictions, capacity, latency, and data quality, \
  rather than deferring them until after a promising backtest?
- Is the stated effort proportionate to what the idea could plausibly earn?

Judge the substance, not the presentation. A longer, more detailed, or more \
confident plan is not automatically better; neither is a shorter one. The two \
plans are shown in a randomised order and their authorship is withheld, so do \
not read anything into which one appears first.

You must choose one plan. Ties are not an available answer; if the plans are \
close, decide on which one is more likely to reach a correct decision about the \
idea, and record your confidence as low."""

_ITEM_TEMPLATE = """\
# Seed research idea

{seed_idea}

# Plan 1

{plan_one}

# Plan 2

{plan_two}

# Your task

Decide whether Plan 1 or Plan 2 is the better research plan for the seed idea \
above, and explain the reasoning that decided it for you."""


class _Verdict(BaseModel):
    """Schema the model is constrained to emit."""

    model_config = ConfigDict(extra="forbid")

    reasoning: str = Field(
        description=(
            "The decisive reasons for the choice, in two to five sentences. "
            "Name the specific strengths and weaknesses that separated the plans."
        )
    )
    preferred_plan: Literal["Plan 1", "Plan 2"] = Field(
        description="The plan you would fund."
    )
    confidence: Confidence = Field(
        description="How clear-cut the choice was."
    )


@dataclass(frozen=True, slots=True)
class Judgement:
    """A model's verdict on one item, mapped back to the A/B labels."""

    item_id: str
    model: str
    order: PresentationOrder
    preference: Preference
    confidence: Confidence
    reasoning: str
    input_tokens: int
    output_tokens: int


@dataclass(frozen=True, slots=True)
class JudgementFailure:
    """A judging attempt that did not produce a usable verdict."""

    item_id: str
    model: str
    order: PresentationOrder
    error: str


JudgeResult = Judgement | JudgementFailure


@dataclass(frozen=True, slots=True)
class ModelCapabilities:
    """Which request features a model's generation accepts."""

    adaptive_thinking: bool
    effort: bool


_ADAPTIVE = ModelCapabilities(adaptive_thinking=True, effort=True)
_LEGACY = ModelCapabilities(adaptive_thinking=False, effort=False)

#: Unknown model ids get the conservative shape. ``thinking`` and ``effort`` are
#: additive, so a stale table degrades a judgement rather than failing the run,
#: whereas sending either to a model that predates it is a 400.
DEFAULT_CAPABILITIES = _LEGACY

MODEL_CAPABILITIES: Mapping[str, ModelCapabilities] = MappingProxyType(
    {
        "claude-fable-5": _ADAPTIVE,
        "claude-opus-5": _ADAPTIVE,
        "claude-opus-4-8": _ADAPTIVE,
        "claude-opus-4-7": _ADAPTIVE,
        "claude-opus-4-6": _ADAPTIVE,
        "claude-sonnet-5": _ADAPTIVE,
        "claude-sonnet-4-6": _ADAPTIVE,
        "claude-haiku-4-5": _LEGACY,
    }
)


def capabilities_for(model: str) -> ModelCapabilities:
    """Capabilities for a model id, tolerating a dated snapshot suffix.

    ``claude-haiku-4-5-20251001`` resolves through the ``claude-haiku-4-5``
    entry. Longest prefix wins, so an id is never claimed by a shorter alias
    that happens to share its opening characters.
    """
    exact = MODEL_CAPABILITIES.get(model)
    if exact is not None:
        return exact
    matches = [alias for alias in MODEL_CAPABILITIES if model.startswith(alias)]
    if not matches:
        return DEFAULT_CAPABILITIES
    return MODEL_CAPABILITIES[max(matches, key=len)]


def request_params(
    model: str, effort: Effort, schema: dict[str, object]
) -> tuple[ThinkingConfigParam | Omit, OutputConfigParam]:
    """The ``thinking``/``output_config`` pair a given model will accept.

    Models older than the 4.6 generation reject both adaptive thinking and
    ``effort``; they keep ``schema``, since structured output is supported on
    every model this project judges with.
    """
    capabilities = capabilities_for(model)
    output_config: OutputConfigParam = {
        "format": {"type": "json_schema", "schema": schema}
    }
    if capabilities.effort:
        output_config["effort"] = effort
    thinking: ThinkingConfigParam | Omit = (
        {"type": "adaptive"} if capabilities.adaptive_thinking else omit
    )
    return thinking, output_config


def build_prompt(item: EvalItem, order: PresentationOrder) -> str:
    """Render the user prompt, placing the plans in the requested order."""
    if order == "as_is":
        plan_one, plan_two = item.plan_a, item.plan_b
    else:
        plan_one, plan_two = item.plan_b, item.plan_a
    return _ITEM_TEMPLATE.format(
        seed_idea=item.seed_idea, plan_one=plan_one, plan_two=plan_two
    )


def _to_preference(preferred_plan: str, order: PresentationOrder) -> Preference:
    """Map the shown position back onto the item's own A/B labels."""
    shown_first: Preference = "A" if order == "as_is" else "B"
    shown_second: Preference = "B" if order == "as_is" else "A"
    return shown_first if preferred_plan == "Plan 1" else shown_second


def judge_item(
    client: anthropic.Anthropic,
    model: str,
    item: EvalItem,
    *,
    order: PresentationOrder = "as_is",
    effort: Effort = "high",
    max_tokens: int = 8000,
) -> JudgeResult:
    """Ask one model to choose between an item's two plans.

    Never raises for API or validation problems; those come back as a
    :class:`JudgementFailure` so one bad call cannot abort a whole run.
    """
    thinking, output_config = request_params(
        model, effort, _Verdict.model_json_schema()
    )
    messages: list[MessageParam] = [
        {"role": "user", "content": build_prompt(item, order)}
    ]

    def failure(error: str) -> JudgementFailure:
        return JudgementFailure(
            item_id=item.item_id, model=model, order=order, error=error
        )

    try:
        with client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            system=SYSTEM_PROMPT,
            messages=messages,
            thinking=thinking,
            output_config=output_config,
        ) as stream:
            response = stream.get_final_message()
    except anthropic.APIError as exc:
        return failure(f"{type(exc).__name__}: {exc}")

    if response.stop_reason == "refusal":
        details = response.stop_details
        category = getattr(details, "category", None) if details else None
        return failure(f"model refused the request (category={category})")
    if response.stop_reason == "max_tokens":
        return failure(f"response truncated at max_tokens={max_tokens}")

    text = next((b.text for b in response.content if b.type == "text"), None)
    if text is None:
        return failure("response contained no text block")

    try:
        verdict = _Verdict.model_validate_json(text)
    except ValidationError as exc:
        return failure(f"verdict did not match the schema: {exc}")

    return Judgement(
        item_id=item.item_id,
        model=model,
        order=order,
        preference=_to_preference(verdict.preferred_plan, order),
        confidence=verdict.confidence,
        reasoning=verdict.reasoning,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
    )


def opposite(order: PresentationOrder) -> PresentationOrder:
    """The presentation order that swaps the two plans relative to ``order``."""
    return cast(PresentationOrder, "swapped" if order == "as_is" else "as_is")
