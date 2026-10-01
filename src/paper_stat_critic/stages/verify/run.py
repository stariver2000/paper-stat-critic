"""verify: Extraction -> Findings, by computation only (no LLM)."""

from paper_stat_critic.model import Document, Extraction, Finding
from paper_stat_critic.stages.verify.checks import CHECKS


def run(extraction: Extraction, document: Document) -> list[Finding]:
    findings: list[Finding] = []
    for check in CHECKS:
        findings.extend(check(extraction, document))
    return findings
