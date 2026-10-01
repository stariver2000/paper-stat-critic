"""extract: Document -> Extraction, using an LLM with a JSON Schema.

Design and measures come from one call over the whole paper. Tests come from
one call per chunk of blocks: asked to list every test of a long paper in a
single answer, the model sometimes stops after a handful (one 78k-character
paper gave 8 tests on one run and 44 on the next), so each call gets a part
short enough to enumerate completely.
"""

import hashlib
from concurrent.futures import ThreadPoolExecutor
from importlib import resources
from string import Template

from pydantic import BaseModel

from paper_stat_critic.model import Block, Document, Extraction, Measure, ReportedTest, StudyDesign
from paper_stat_critic.ports import LLMClient

SYSTEM_PROMPT = (
    "You are a meticulous research-methods assistant. You extract what a paper "
    "reports about its statistics. You do not evaluate or correct it."
)


class _DesignAnswer(BaseModel):
    design: StudyDesign
    measures: list[Measure]


class _TestsAnswer(BaseModel):
    tests: list[ReportedTest]


def _template(name: str) -> str:
    package_files = resources.files(__package__)
    return package_files.joinpath(name).read_text(encoding="utf-8")


def prompt_fingerprint(chunk_chars: int) -> str:
    """Changes with any prompt, schema or chunk size, so stale cached extractions are redone."""
    parts = [
        SYSTEM_PROMPT,
        _template("prompt_design.md"),
        _template("prompt_tests.md"),
        str(_DesignAnswer.model_json_schema()),
        str(_TestsAnswer.model_json_schema()),
        str(chunk_chars),
    ]
    material = "\x1f".join(parts)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]


def render_blocks(blocks: list[Block]) -> str:
    lines = [f"[{block.id}] {block.text}" for block in blocks]
    return "\n\n".join(lines)


def build_prompt(template_name: str, blocks: list[Block]) -> str:
    template = Template(_template(template_name))
    return template.safe_substitute(document=render_blocks(blocks))


def chunk_blocks(blocks: list[Block], chunk_chars: int) -> list[list[Block]]:
    """Group consecutive blocks into chunks of at most `chunk_chars` characters.

    Blocks are never split, so a reported test stays inside one chunk. A single
    block longer than the limit becomes a chunk of its own.
    """
    chunks: list[list[Block]] = []
    current: list[Block] = []
    size = 0
    for block in blocks:
        if current and size + len(block.text) > chunk_chars:
            chunks.append(current)
            current = []
            size = 0
        current.append(block)
        size += len(block.text)
    if current:
        chunks.append(current)
    return chunks


def merge_tests(parts: list[list[ReportedTest]]) -> list[ReportedTest]:
    """Concatenate chunk answers in document order, drop exact repeats, renumber T1..Tn.

    Exact repeats (same statistic, df and p) come from a result restated in
    the abstract or discussion; keeping both would report the same problem twice.
    """
    merged: list[ReportedTest] = []
    seen: set[tuple] = set()
    for tests in parts:
        for test in tests:
            key = (test.kind, test.df1, test.df2, test.statistic, test.p_comparator, test.p_value)
            if key in seen:
                continue
            seen.add(key)
            merged.append(test)
    renumbered = []
    for index, test in enumerate(merged, start=1):
        renumbered.append(test.model_copy(update={"id": f"T{index}"}))
    return renumbered


def run(document: Document, llm: LLMClient, chunk_chars: int, workers: int) -> Extraction:
    design_schema = _DesignAnswer.model_json_schema()
    tests_schema = _TestsAnswer.model_json_schema()

    def ask_design() -> _DesignAnswer:
        prompt = build_prompt("prompt_design.md", document.blocks)
        raw = llm.complete_json(SYSTEM_PROMPT, prompt, design_schema)
        return _DesignAnswer.model_validate(raw)

    def ask_tests(blocks: list[Block]) -> list[ReportedTest]:
        prompt = build_prompt("prompt_tests.md", blocks)
        raw = llm.complete_json(SYSTEM_PROMPT, prompt, tests_schema)
        return _TestsAnswer.model_validate(raw).tests

    # Calls are independent, so they run concurrently; map() keeps chunk order.
    chunks = chunk_blocks(document.blocks, chunk_chars)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        design_future = pool.submit(ask_design)
        test_parts = list(pool.map(ask_tests, chunks))
        design_answer = design_future.result()

    return Extraction(
        design=design_answer.design,
        measures=design_answer.measures,
        tests=merge_tests(test_parts),
    )
