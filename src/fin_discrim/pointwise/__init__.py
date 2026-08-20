"""Pointwise assessment of a single plan and its critique.

Where :mod:`fin_discrim.judge` asks a model to choose between two competing
plans, this package scores one submission on its own terms, against a suite of
named dimensions. Add a dimension in :mod:`fin_discrim.pointwise.dimensions`.
"""

from __future__ import annotations

from fin_discrim.pointwise.assess import (
    AssessResult,
    DimensionScore,
    ScoreFailure,
    assess_dimension,
)
from fin_discrim.pointwise.dimensions import DIMENSIONS, Dimension, Target
from fin_discrim.pointwise.scoring import DimensionSummary, summarise

__all__ = [
    "DIMENSIONS",
    "AssessResult",
    "Dimension",
    "DimensionScore",
    "DimensionSummary",
    "ScoreFailure",
    "Target",
    "assess_dimension",
    "summarise",
]
