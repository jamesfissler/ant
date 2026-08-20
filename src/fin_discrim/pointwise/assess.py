"""Scoring one plan or critique on one dimension, with one model call.

The gold preference and the expert scores are never referenced here: an
assessor sees the seed idea, the submission under assessment, and the single
dimension it is being asked about.
"""

from __future__ import annotations

from dataclasses import dataclass

import anthropic
from anthropic.types import MessageParam
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from fin_discrim.items import EvalItem, Side
from fin_discrim.judge import Effort, request_params
from fin_discrim.pointwise.dimensions import SCALE, Dimension, Score

SYSTEM_PROMPT = """\
You are a senior research director at a systematic investment manager, \
assessing one submission against one stated criterion.

Score only the criterion you are given. Other qualities of the submission, \
however good or bad, are out of scope for this score.

Judge the substance, not the presentation. A longer, more detailed, or more \
confident submission is not automatically better; neither is a shorter one. \
Assume a working research platform and market data already exist, so the \
absence of infrastructure-building is not a weakness.

Use the whole scale. Most competent work sits at 3 or 4; reserve 5 for a \
submission that also handles what is usually missed, and 1 for one that does \
not engage with the criterion at all."""

_PLAN_TEMPLATE = """\
# Seed research idea

{seed_idea}

# The plan under assessment

{plan}"""

_CRITIQUE_TEMPLATE = """\
# Seed research idea

{seed_idea}

# The plan the critique is about

{plan}

# The critique under assessment

{critique}"""

_TASK_TEMPLATE = """\
# Your task

Score the {subject} above on this criterion alone.

## {title}

{question}

{guidance}

## Scale

{scale}"""


class _Assessment(BaseModel):
    """Schema the model is constrained to emit."""

    model_config = ConfigDict(extra="forbid")

    justification: str = Field(
        description=(
            "The evidence for the score, in two to four sentences. Quote or "
            "name the specific passages that decided it."
        )
    )
    score: Score = Field(description="The score on the 1-5 scale.")


@dataclass(frozen=True, slots=True)
class DimensionScore:
    """One model's score for one dimension of one submission."""

    item_id: str
    model: str
    side: Side
    dimension: str
    score: int
    justification: str
    input_tokens: int
    output_tokens: int


@dataclass(frozen=True, slots=True)
class ScoreFailure:
    """An assessment that did not produce a usable score."""

    item_id: str
    model: str
    side: Side
    dimension: str
    error: str


AssessResult = DimensionScore | ScoreFailure


def build_prompt(item: EvalItem, side: Side, dimension: Dimension) -> str:
    """Render the user prompt for one dimension of one side of an item.

    A critique is shown with the plan it criticises, since it cannot be judged
    without it. A plan is shown on its own, so that a weak critique cannot drag
    down the plan's own scores.
    """
    if dimension.target == "plan":
        context = _PLAN_TEMPLATE.format(seed_idea=item.seed_idea, plan=item.plan(side))
        subject = "plan"
    else:
        context = _CRITIQUE_TEMPLATE.format(
            seed_idea=item.seed_idea,
            plan=item.plan(side),
            critique=item.critique(side),
        )
        subject = "critique"
    task = _TASK_TEMPLATE.format(
        subject=subject,
        title=dimension.title,
        question=dimension.question,
        guidance=dimension.guidance,
        scale=SCALE,
    )
    return f"{context}\n\n{task}"


def assess_dimension(
    client: anthropic.Anthropic,
    model: str,
    item: EvalItem,
    dimension: Dimension,
    *,
    side: Side = "A",
    effort: Effort = "high",
    max_tokens: int = 8000,
) -> AssessResult:
    """Score one submission on one dimension.

    Never raises for API or validation problems; those come back as a
    :class:`ScoreFailure` so one bad call cannot abort a whole run.
    """
    thinking, output_config = request_params(
        model, effort, _Assessment.model_json_schema()
    )
    messages: list[MessageParam] = [
        {"role": "user", "content": build_prompt(item, side, dimension)}
    ]

    def failure(error: str) -> ScoreFailure:
        return ScoreFailure(
            item_id=item.item_id,
            model=model,
            side=side,
            dimension=dimension.key,
            error=error,
        )

    if dimension.target == "critique" and not item.critique(side).strip():
        return failure(f"item has no critique_{side} to assess")

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
        assessment = _Assessment.model_validate_json(text)
    except ValidationError as exc:
        return failure(f"assessment did not match the schema: {exc}")

    return DimensionScore(
        item_id=item.item_id,
        model=model,
        side=side,
        dimension=dimension.key,
        score=assessment.score,
        justification=assessment.justification,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
    )
