"""extract: Document -> Extraction, using an LLM with a JSON Schema."""

import hashlib
from importlib import resources
from string import Template

from paper_stat_critic.model import Document, Extraction
from paper_stat_critic.ports import LLMClient

SYSTEM_PROMPT = (
    "You are a meticulous research-methods assistant. You extract what a paper "
    "reports about its statistics. You do not evaluate or correct it."
)


def _prompt_template() -> str:
    package_files = resources.files(__package__)
    return package_files.joinpath("prompt.md").read_text(encoding="utf-8")


def prompt_fingerprint() -> str:
    """Changes whenever the prompt or schema changes, so cached extractions are redone."""
    schema_text = str(Extraction.model_json_schema())
    material = SYSTEM_PROMPT + _prompt_template() + schema_text
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]


def render_document(document: Document) -> str:
    lines = [f"[{block.id}] {block.text}" for block in document.blocks]
    return "\n\n".join(lines)


def build_prompt(document: Document) -> str:
    template = Template(_prompt_template())
    return template.safe_substitute(document=render_document(document))


def run(document: Document, llm: LLMClient) -> Extraction:
    schema = Extraction.model_json_schema()
    raw = llm.complete_json(SYSTEM_PROMPT, build_prompt(document), schema)
    return Extraction.model_validate(raw)
