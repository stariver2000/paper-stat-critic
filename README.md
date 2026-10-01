# paper-stat-critic

Critical statistical review of research papers.

Give it a PDF; it extracts every reported test (t, F, χ², r, z) and the study
design, recomputes the p-values from the printed statistics, and flags
inconsistencies. The goal is a reviewer that is *hard to fool*: an LLM reads
the paper, but every claim it makes is either checked by code or, in later
stages, challenged by a second adversarial pass.

> **Status: early.** The `ingest → extract → verify` stages work. The
> rubric-based `assess` stage, the adversarial `rebut` stage and HTML reports
> are on the [roadmap](docs/DESIGN.md#roadmap). Contributions welcome.

## How it works

```
PDF ─▶ ingest ─▶ extract ─▶ verify ─▶ (assess ─▶ rebut ─▶ report)
       blocks    LLM →       code only:
       with ids  JSON        · p recomputed from statistic + df (statcheck-style)
                 + quotes    · every LLM quote checked against the source text
```

Each stage writes a numbered artifact to `runs/<paper_id>/`
(`01_document.json`, `02_extraction.json`, `03_verify.json`), so you can read
the flow file by file. LLM outputs are cached; rerunning after a code change
costs nothing.

## Requirements

- Python 3.12+ and [uv](https://docs.astral.sh/uv/)
- The [Claude Code](https://claude.com/claude-code) CLI, logged in
  (`claude` on your PATH). The tool calls `claude -p` in headless mode, so it
  runs on your existing Claude login. **This project never reads or stores
  an API key.**

## Usage

```bash
uv sync
uv run paper-stat-critic run path/to/paper.pdf
uv run paper-stat-critic run paper.pdf --until extract   # stop before checks
uv run paper-stat-critic batch papers/ --limit 10
```

Example output:

```
smith-2024-hri-1a2b3c4d  ->  runs/smith-2024-hri-1a2b3c4d
  extracted 14 tests
  [high  ] T7: p inconsistent and the significance decision flips
  [low   ] T3: p matches only a one-tailed test
```

## Privacy and copyright

- `runs/` holds the full text of the papers you review and is git-ignored.
  Do not commit it, and do not attach it to issues.
- PDFs are git-ignored. Tests generate their PDFs in code.
- Paper text is sent to the model through your own Claude CLI login.
  Do not review unpublished manuscripts you are not allowed to share.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). The architecture is described in
[docs/DESIGN.md](docs/DESIGN.md).

## License

[MIT](LICENSE)
