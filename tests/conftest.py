"""Shared builders. Tests never touch a real LLM or a real paper."""

from typing import Any

from paper_stat_critic.model import (
    Document,
    Evidence,
    Extraction,
    PComparator,
    ReportedTest,
    StatisticKind,
    StudyDesign,
)
from paper_stat_critic.model.document import Block
from paper_stat_critic.ports import PageText


def make_test(
    kind: StatisticKind,
    statistic: str,
    p_value: str,
    df1: float | None = None,
    df2: float | None = None,
    comparator: PComparator = PComparator.EQ,
    test_id: str = "T1",
    quote: str = "quote",
) -> ReportedTest:
    return ReportedTest(
        id=test_id,
        analysis="test",
        kind=kind,
        df1=df1,
        df2=df2,
        statistic=statistic,
        p_comparator=comparator,
        p_value=p_value,
        evidence=Evidence(quote=quote, block_id=None),
    )


def make_extraction(tests: list[ReportedTest]) -> Extraction:
    design = StudyDesign(
        n_participants=None, factors=[], multiple_trials_per_condition=None, evidence=[]
    )
    return Extraction(design=design, measures=[], tests=tests)


def make_document(text: str) -> Document:
    block = Block(id="p1b1", page=1, text=text)
    return Document(paper_id="paper", blocks=[block])


class FakeParser:
    def __init__(self, pages: list[str]) -> None:
        self._pages = pages

    def parse(self, pdf: bytes) -> list[PageText]:
        return [PageText(page=i + 1, text=text) for i, text in enumerate(self._pages)]


class FakeLLM:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.calls: list[str] = []

    @property
    def fingerprint(self) -> str:
        return "fake:1"

    def complete_json(self, system: str, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        self.calls.append(prompt)
        return self.response
