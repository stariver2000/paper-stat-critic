"""Interfaces the stages depend on; concrete adapters live in `adapters/`.

Stages only see these protocols, so swapping the Claude CLI for the
Anthropic API, or pdfium for another parser, never touches stage code.
"""

from typing import Any, NamedTuple, Protocol


class PageText(NamedTuple):
    page: int
    text: str


class PdfParser(Protocol):
    def parse(self, pdf: bytes) -> list[PageText]: ...


class LLMError(RuntimeError):
    pass


class LLMClient(Protocol):
    def complete_json(self, system: str, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        """Return an object matching `schema`, or raise LLMError."""
        ...

    @property
    def fingerprint(self) -> str:
        """Identifies backend + model, so cached outputs of another model are not reused."""
        ...
