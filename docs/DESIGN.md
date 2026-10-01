# Design

This is the single design document. It describes the code as it is; planned
work is confined to the [Roadmap](#roadmap) section.

## Goal

A statistical reviewer that is hard to fool. An LLM reads the paper, but the
LLM is used for **reading and phrasing**, while **checking is done by code**
wherever possible. Every extracted item carries a verbatim quote so a human
can verify it in seconds.

## Architecture

Layered at the top level, a pipeline in the middle, ports and adapters at
the edges.

```
interfaces/   CLI (later: HTTP)            ← parses flags, prints results
     │
pipeline/     order, caching, file I/O     ← the only layer that touches disk
     │
stages/       ingest → extract → verify    ← pure functions over model objects
     │              │
model/        shared types          ports.py  LLMClient, PdfParser protocols
                                         ▲
adapters/     claude_cli, pdfium_parser  ┘  ← chosen by pipeline, injected into stages
```

Dependency rules:

1. Imports flow downward only. `model/` imports nothing from this package.
2. Stages never import each other, never read or write files, and only see
   the protocols in `ports.py`, never a concrete adapter.
3. Checks inside `stages/verify/checks/` never import each other.
4. Each package exposes its public API from its `__init__.py`.

MVC was not chosen: there is no interactive view or user-facing state. The
core is a data transformation, which a pipeline expresses directly.

## Stages

| # | Stage   | Input → Output              | LLM | Cached | Artifact             |
|---|---------|-----------------------------|-----|--------|----------------------|
| 1 | ingest  | PDF bytes → `Document`      | no  | no     | `01_document.json`   |
| 2 | extract | `Document` → `Extraction`   | yes | yes    | `02_extraction.json` |
| 3 | verify  | `Extraction` → `[Finding]`  | no  | no     | `03_verify.json`     |

**ingest** splits each page into paragraph-sized blocks with ids `p{page}b{n}`.
The LLM cites these ids, so they must be stable for the same PDF.

**extract** sends the blocks plus the JSON Schema of `model.Extraction` to
the LLM. Field descriptions in `model/extraction.py` are part of the prompt.

**verify** runs every check registered in `stages/verify/checks/__init__.py`:

- `quote_anchor`: each evidence quote must occur in the parsed text
  (compared after dropping case, punctuation and whitespace).
- `pvalue_recompute`: statcheck-style. A reported p is consistent if any
  statistic that rounds to the printed one yields it. Severity:
  `high` if the significance decision at α = .05 flips, `low` if only a
  one-tailed reading matches, otherwise `medium`.

## Caching

Only LLM stages are cached; deterministic stages always rerun so a code
change never leaves a stale result. The extract cache key hashes the
document, the prompt + schema (`extract.prompt_fingerprint()`) and the LLM
fingerprint (backend + model). Changing any of them invalidates the cache.
`--force` ignores it.

## LLM backend

`adapters/claude_cli.py` calls `claude -p --output-format json --json-schema`
and reads `structured_output`. It runs in an empty temporary directory with
tools, settings sources, MCP servers, skills and session persistence
disabled, so results do not depend on the caller's environment. It uses the
CLI's own login; the project never handles an API key.

## Roadmap

Planned, not implemented. Each item lands as a new stage directory plus a
registry entry.

1. **assess**: match `Extraction.design` and `measures` against rubric rules
   in `rubric/*.yaml` (e.g. within-subject factor analysed with an
   independent-samples test; single Likert item analysed with ANOVA). Rules
   whose condition is computable run as code; the rest go to the LLM.
   Findings gain a `source` field (`verify` / `rubric` / `llm`).
2. **rebut**: a second LLM call tries to refute each LLM-originated finding;
   only survivors are reported. Code-originated findings skip this.
3. **report**: Markdown/HTML report ordered by severity with quotes.
4. More verify checks: GRIM, df vs. N consistency, multiple-comparison
   count, effect size / CI reporting.
5. Alternative adapters: Anthropic API client, a parser with table support.
6. HTTP interface (FastAPI) as a job API: `POST /reviews`,
   `GET /reviews/{id}`, `GET /reviews/{id}/stages/{stage}`.
