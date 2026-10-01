"""Shared intermediate representation passed between pipeline stages.

This package imports nothing else from paper_stat_critic, so every stage,
adapter and interface can depend on it without creating cycles.
"""

from paper_stat_critic.model.document import Block, Document
from paper_stat_critic.model.evidence import Evidence
from paper_stat_critic.model.extraction import (
    Assignment,
    Extraction,
    Factor,
    Measure,
    MeasureScale,
    PComparator,
    ReportedTest,
    StatisticKind,
    StudyDesign,
)
from paper_stat_critic.model.finding import Finding, Severity

__all__ = [
    "Assignment",
    "Block",
    "Document",
    "Evidence",
    "Extraction",
    "Factor",
    "Finding",
    "Measure",
    "MeasureScale",
    "PComparator",
    "ReportedTest",
    "Severity",
    "StatisticKind",
    "StudyDesign",
]
