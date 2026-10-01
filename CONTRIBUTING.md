# Contributing

Thanks for helping. Good first contributions: a new deterministic check, a
rubric rule (once `assess` lands), or a failing case from a real paper.

## Setup

```bash
uv sync
uv run pre-commit install     # runs ruff + gitleaks before every commit
uv run pytest
```

Tests never call an LLM; they use fakes from `tests/conftest.py`. You do not
need the Claude CLI to contribute code.

## Workflow

1. Fork, branch from `main`, open a pull request.
2. CI must pass: `lint`, `test`, `secrets`.
3. One approving review from a maintainer is required to merge.

## Where does my code go?

| You are adding…                     | Put it in                                        |
|-------------------------------------|--------------------------------------------------|
| A deterministic check               | `stages/verify/checks/<name>.py` + register in `checks/__init__.py` |
| A new pipeline stage                | `stages/<name>/` + entry in `pipeline/registry.py` and `runner.py` |
| A new LLM backend or PDF parser     | `adapters/<name>.py` implementing a protocol in `ports.py` |
| A new field passed between stages   | `model/`                                         |
| A new command                       | `interfaces/cli.py`                              |

Tests mirror the source tree: `src/paper_stat_critic/stages/verify/checks/grim.py`
→ `tests/stages/verify/checks/test_grim.py`.

## Code rules

Readability
- If one expression nests three or more constructs, split it into named
  intermediate variables.
- No comprehensions combining several conditions, walrus or nested calls.
- Prefer code where input, transformation and output are visible over short code.

Comments
- Explain *why* the code is there, not what it does.
- Comment wherever data changes meaning (text normalization, rounding
  intervals, unit conversions).
- A field or parameter unused by current code must say which feature uses
  it and when. Otherwise leave it out.

Structure
- Dependencies flow one way: `interfaces → pipeline → stages → model`.
  `model/` imports nothing from this package.
- Stages and checks never import each other; shared logic moves down a layer.
- Stages are pure: no file I/O. Paths and settings are injected.
- Import other packages only through their `__init__.py`.
- One responsibility per file. Past ~500 lines, split.

Cleanup
- Every change cleans up after itself: no compatibility shims, no dead code,
  no commented-out old versions (Git keeps history).
- Keep `docs/DESIGN.md` in sync with the code in the same PR.

## Never commit

- API keys, tokens, `.env` files, credentials of any kind.
- Paper PDFs or anything from `runs/` (copyrighted paper text).
- Absolute paths from your machine, personal emails, or names of people in
  reviewed papers' unpublished data.

`gitleaks` runs in pre-commit and in CI. If it flags a real secret, rotate
the secret first; deleting the commit is not enough once it was pushed.
