"""humanvals — human feedback -> verified agent memory.

Two-call integration:

    from humanvals import HumanVals

    hv = HumanVals('humanvals.db')
    gs = hv.guidelines(user_input, agent='my-bot')   # retrieval, '' at cold start
    ... run your agent with gs.as_prompt() appended ...
    hv.record_case(agent='my-bot', input=user_input, output=result, guidelines=gs)

Docs: https://github.com/alinaqi/humanvals — RFC in docs/HumanVals_RFC.md.
"""

from humanvals.client import HumanVals
from humanvals.embedding import Embedder, HashedNgramEmbedder
from humanvals.metrics import GuidelineImpact, InterventionReport, Metrics
from humanvals.models import (
    Budget,
    Case,
    EvalResult,
    Evaluation,
    Guideline,
    GuidelineSet,
    PromotionPolicy,
)

__version__ = '0.1.0'

__all__ = [
    'Budget',
    'Case',
    'Embedder',
    'EvalResult',
    'Evaluation',
    'Guideline',
    'GuidelineImpact',
    'GuidelineSet',
    'HashedNgramEmbedder',
    'HumanVals',
    'InterventionReport',
    'Metrics',
    'PromotionPolicy',
]
