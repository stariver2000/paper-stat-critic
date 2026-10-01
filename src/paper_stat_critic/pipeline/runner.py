"""Runs the stages in order, wiring outputs to inputs and handling all file I/O.

Only stages that call an LLM are cached: they are slow and spend quota.
Deterministic stages are cheap and always rerun, so a code change in a
check never leaves a stale result behind.
"""

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from paper_stat_critic.adapters import ClaudeCliClient, PdfiumParser
from paper_stat_critic.model import Document, Extraction, Finding
from paper_stat_critic.pipeline.config import ReviewConfig
from paper_stat_critic.pipeline.registry import StageName, stages_until
from paper_stat_critic.pipeline.store import RunStore
from paper_stat_critic.ports import LLMClient, PdfParser
from paper_stat_critic.stages import extract, ingest, verify


@dataclass(frozen=True)
class Adapters:
    parser: PdfParser
    llm: LLMClient


@dataclass(frozen=True)
class RunResult:
    paper_id: str
    run_dir: Path
    document: Document
    extraction: Extraction | None
    findings: list[Finding] | None
    extraction_cached: bool


def build_adapters(config: ReviewConfig) -> Adapters:
    llm = ClaudeCliClient(
        binary=config.claude_binary,
        model=config.model,
        timeout_s=config.llm_timeout_s,
    )
    return Adapters(parser=PdfiumParser(), llm=llm)


def make_paper_id(file_name: str, pdf: bytes) -> str:
    """Readable and collision-free: slug of the file name plus a content hash."""
    stem = Path(file_name).stem.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", stem).strip("-")[:60]
    digest = hashlib.sha256(pdf).hexdigest()[:8]
    return f"{slug}-{digest}"


def _hash(*parts: str) -> str:
    joined = "\x1f".join(parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:16]


def run_pipeline(
    pdf_path: Path,
    config: ReviewConfig,
    adapters: Adapters,
    until: StageName = StageName.VERIFY,
    force: bool = False,
) -> RunResult:
    pdf = pdf_path.read_bytes()
    paper_id = make_paper_id(pdf_path.name, pdf)
    store = RunStore(config.runs_dir, paper_id)
    stages = stages_until(until)

    document = ingest.run(pdf, paper_id, adapters.parser)
    document_key = _hash(document.model_dump_json())
    store.save(StageName.INGEST, document, Document, document_key)

    extraction: Extraction | None = None
    extraction_cached = False
    if StageName.EXTRACT in stages:
        # The key covers the document, the prompt+schema and the model, so
        # editing any of them invalidates the stored extraction.
        prompt_key = extract.prompt_fingerprint(config.extract_chunk_chars)
        extract_key = _hash(document_key, prompt_key, adapters.llm.fingerprint)
        if not force:
            extraction = store.load(StageName.EXTRACT, Extraction, extract_key)
        extraction_cached = extraction is not None
        if extraction is None:
            extraction = extract.run(
                document, adapters.llm, config.extract_chunk_chars, config.llm_workers
            )
            store.save(StageName.EXTRACT, extraction, Extraction, extract_key)

    findings: list[Finding] | None = None
    if StageName.VERIFY in stages and extraction is not None:
        findings = verify.run(extraction, document)
        store.save(StageName.VERIFY, findings, list[Finding], "")

    return RunResult(
        paper_id=paper_id,
        run_dir=store.run_dir,
        document=document,
        extraction=extraction,
        findings=findings,
        extraction_cached=extraction_cached,
    )
