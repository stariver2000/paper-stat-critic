"""Command-line entry point. Translates flags into a ReviewConfig and prints results."""

from pathlib import Path

import typer

from paper_stat_critic import ReviewConfig, RunResult, StageName, build_adapters, run_pipeline

app = typer.Typer(no_args_is_help=True, help="Critical statistical review of research papers.")

RunsDir = typer.Option(Path("runs"), help="Where per-paper artifacts are written.")
Model = typer.Option("sonnet", help="Model alias passed to `claude --model`.")
Until = typer.Option(StageName.VERIFY, help="Last stage to run.")
Force = typer.Option(False, help="Ignore cached LLM outputs.")


def _print_result(result: RunResult) -> None:
    typer.echo(f"{result.paper_id}  ->  {result.run_dir}")
    if result.extraction is not None:
        cached = " (cached)" if result.extraction_cached else ""
        typer.echo(f"  extracted {len(result.extraction.tests)} tests{cached}")
    if result.findings is None:
        return
    if not result.findings:
        typer.echo("  no findings")
    for finding in result.findings:
        typer.echo(f"  [{finding.severity.value:6}] {finding.title}")


@app.command()
def run(
    pdf: Path,
    runs_dir: Path = RunsDir,
    model: str = Model,
    until: StageName = Until,
    force: bool = Force,
) -> None:
    """Review one PDF."""
    config = ReviewConfig(runs_dir=runs_dir, model=model)
    result = run_pipeline(pdf, config, build_adapters(config), until=until, force=force)
    _print_result(result)


@app.command()
def batch(
    directory: Path,
    limit: int = typer.Option(10, help="Maximum number of PDFs to process."),
    runs_dir: Path = RunsDir,
    model: str = Model,
    until: StageName = Until,
    force: bool = Force,
) -> None:
    """Review every PDF under a directory (recursively), up to --limit."""
    config = ReviewConfig(runs_dir=runs_dir, model=model)
    adapters = build_adapters(config)
    pdfs = sorted(directory.rglob("*.pdf"))[:limit]
    for pdf in pdfs:
        # One unreadable PDF or LLM failure should not stop a batch that may
        # take an hour; it is reported and the next paper runs. The catch is
        # broad because PDF libraries raise their own exception types.
        try:
            result = run_pipeline(pdf, config, adapters, until=until, force=force)
        except Exception as error:
            typer.echo(f"{pdf.name}: FAILED ({error})", err=True)
            continue
        _print_result(result)
