"""Run settings, always injected from outside (CLI flags, tests)."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ReviewConfig:
    runs_dir: Path
    claude_binary: str = "claude"
    model: str = "sonnet"
    llm_timeout_s: float = 600.0
    # Characters per test-extraction call. Small enough that the model lists
    # every test in its part; see stages/extract/run.py.
    extract_chunk_chars: int = 15_000
    # Concurrent LLM calls within one paper.
    llm_workers: int = 4
