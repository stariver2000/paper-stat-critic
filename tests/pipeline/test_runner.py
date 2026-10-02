from paper_stat_critic import Adapters, ReviewConfig, StageName, run_pipeline
from paper_stat_critic.model import StatisticKind
from paper_stat_critic.pipeline.runner import make_paper_id
from tests.conftest import FakeLLM, FakeParser, make_extraction, make_test

PAGE = "Participants rated the robot, t(28) = 1.80, p = .04."


def setup(tmp_path):
    pdf_path = tmp_path / "My Paper.pdf"
    pdf_path.write_bytes(b"pdf-bytes")
    test = make_test(StatisticKind.T, "1.80", ".04", df1=28, quote="t(28) = 1.80, p = .04")
    llm = FakeLLM(make_extraction([test]).model_dump(mode="json"))
    adapters = Adapters(parser=FakeParser([PAGE]), llm=llm)
    config = ReviewConfig(runs_dir=tmp_path / "runs")
    return pdf_path, config, adapters, llm


def test_full_run_writes_numbered_artifacts(tmp_path):
    pdf_path, config, adapters, _ = setup(tmp_path)
    result = run_pipeline(pdf_path, config, adapters)
    names = sorted(path.name for path in result.run_dir.iterdir())
    assert names == ["01_document.json", "02_extraction.json", "03_verify.json"]
    assert [finding.check for finding in result.findings] == ["pvalue_recompute"]


def test_extraction_is_cached(tmp_path):
    pdf_path, config, adapters, llm = setup(tmp_path)
    run_pipeline(pdf_path, config, adapters)
    calls_after_first = len(llm.calls)
    second = run_pipeline(pdf_path, config, adapters)
    assert len(llm.calls) == calls_after_first
    assert second.extraction_cached


def test_force_ignores_cache(tmp_path):
    pdf_path, config, adapters, llm = setup(tmp_path)
    run_pipeline(pdf_path, config, adapters)
    calls_after_first = len(llm.calls)
    run_pipeline(pdf_path, config, adapters, force=True)
    assert len(llm.calls) == 2 * calls_after_first


def test_until_ingest_skips_llm(tmp_path):
    pdf_path, config, adapters, llm = setup(tmp_path)
    result = run_pipeline(pdf_path, config, adapters, until=StageName.INGEST)
    assert llm.calls == []
    assert result.extraction is None


def test_paper_id_is_slug_plus_hash():
    paper_id = make_paper_id("My Paper (2024).pdf", b"x")
    assert paper_id.startswith("my-paper-2024-")
    assert len(paper_id.rsplit("-", 1)[1]) == 8
