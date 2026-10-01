"""Flag evidence quotes that do not occur in the paper.

Every other judgement rests on the extraction, so a quote the LLM made up
(or paraphrased) is the first thing a reader needs to know about.
"""

import unicodedata

from paper_stat_critic.model import Document, Evidence, Extraction, Finding, Severity

NAME = "quote_anchor"


def compact(text: str) -> str:
    """Reduce text to lowercase letters and digits for robust matching.

    PDF extraction and LLM copying disagree on hyphenation, line breaks,
    quote marks and minus signs; none of those change what was said, so all
    punctuation and whitespace are dropped before comparing.
    """
    normalized = unicodedata.normalize("NFKC", text).casefold()
    kept = [char for char in normalized if char.isalnum()]
    return "".join(kept)


def _all_evidence(extraction: Extraction) -> list[tuple[str, Evidence]]:
    pairs: list[tuple[str, Evidence]] = []
    for evidence in extraction.design.evidence:
        pairs.append(("design", evidence))
    for measure in extraction.measures:
        pairs.append((f"measure '{measure.name}'", measure.evidence))
    for test in extraction.tests:
        pairs.append((f"test {test.id}", test.evidence))
    return pairs


def check(extraction: Extraction, document: Document) -> list[Finding]:
    source = compact(document.full_text())
    findings: list[Finding] = []
    for owner, evidence in _all_evidence(extraction):
        if compact(evidence.quote) in source:
            continue
        test_ids = [owner.removeprefix("test ")] if owner.startswith("test ") else []
        findings.append(
            Finding(
                check=NAME,
                severity=Severity.MEDIUM,
                title=f"Quote for {owner} not found in the paper",
                detail=(
                    "The extracted evidence does not occur verbatim in the parsed text. "
                    "It may be paraphrased or invented; treat this item's values with caution."
                ),
                test_ids=test_ids,
                evidence=[evidence],
            )
        )
    return findings
