"""Registry of deterministic checks.

To add a check: create one module here exposing
`check(extraction, document) -> list[Finding]`, then append it to CHECKS.
Checks never import each other.
"""

from collections.abc import Callable

from paper_stat_critic.model import Document, Extraction, Finding
from paper_stat_critic.stages.verify.checks import pvalue_recompute, quote_anchor

Check = Callable[[Extraction, Document], list[Finding]]

CHECKS: list[Check] = [
    quote_anchor.check,
    pvalue_recompute.check,
]
