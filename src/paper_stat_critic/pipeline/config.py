"""Run settings, always injected from outside (CLI flags, tests)."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ReviewConfig:
    runs_dir: Path
    claude_binary: str = "claude"
    model: str = "sonnet"
    llm_timeout_s: float = 600.0
