"""A problem a stage found in the paper."""

from enum import StrEnum

from pydantic import BaseModel

from paper_stat_critic.model.evidence import Evidence


class Severity(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Finding(BaseModel):
    check: str
    severity: Severity
    title: str
    detail: str
    test_ids: list[str]
    evidence: list[Evidence]
