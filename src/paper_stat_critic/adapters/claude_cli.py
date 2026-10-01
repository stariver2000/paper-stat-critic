"""LLMClient that shells out to the Claude Code CLI (`claude -p`).

This uses the CLI's own login (e.g. a Claude subscription), so no API key
is read, stored or passed by this project.
"""

import json
import subprocess
import tempfile
from typing import Any

from paper_stat_critic.ports import LLMError

# Each flag strips something the CLI would otherwise bring into a one-shot
# extraction call: tools (the paper text is already in the prompt), the
# user's settings and MCP servers (results must not depend on who runs it),
# skills, and session files on disk.
_ISOLATION_FLAGS = [
    "--tools",
    "",
    "--strict-mcp-config",
    "--setting-sources",
    "",
    "--disable-slash-commands",
    "--no-session-persistence",
]


def parse_cli_output(stdout: str) -> dict[str, Any]:
    """Pull the structured object out of `claude -p --output-format json` output."""
    try:
        envelope = json.loads(stdout)
    except json.JSONDecodeError as error:
        raise LLMError(f"claude CLI did not return JSON: {stdout[:200]!r}") from error

    if envelope.get("is_error"):
        raise LLMError(f"claude CLI reported an error: {envelope.get('result')!r}")

    structured = envelope.get("structured_output")
    if not isinstance(structured, dict):
        raise LLMError("claude CLI response has no structured_output object")
    return structured


class ClaudeCliClient:
    def __init__(self, binary: str, model: str, timeout_s: float) -> None:
        self._binary = binary
        self._model = model
        self._timeout_s = timeout_s

    @property
    def fingerprint(self) -> str:
        return f"claude-cli:{self._model}"

    def complete_json(self, system: str, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        command = [
            self._binary,
            "-p",
            "--output-format",
            "json",
            "--model",
            self._model,
            "--system-prompt",
            system,
            "--json-schema",
            json.dumps(schema),
            *_ISOLATION_FLAGS,
        ]
        # The prompt goes through stdin because a full paper can exceed the
        # OS limit on argument length. An empty temporary cwd keeps any
        # CLAUDE.md or project settings near the caller out of the context.
        with tempfile.TemporaryDirectory() as empty_dir:
            try:
                completed = subprocess.run(
                    command,
                    input=prompt,
                    capture_output=True,
                    text=True,
                    cwd=empty_dir,
                    timeout=self._timeout_s,
                    check=False,
                )
            except FileNotFoundError as error:
                raise LLMError(f"claude CLI not found at {self._binary!r}") from error
            except subprocess.TimeoutExpired as error:
                raise LLMError(f"claude CLI timed out after {self._timeout_s}s") from error

        if completed.returncode != 0 and not completed.stdout:
            raise LLMError(f"claude CLI exited {completed.returncode}: {completed.stderr[:500]}")
        return parse_cli_output(completed.stdout)
