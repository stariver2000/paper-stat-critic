from paper_stat_critic.model import Extraction
from paper_stat_critic.stages import extract
from paper_stat_critic.stages.extract.run import build_prompt
from tests.conftest import FakeLLM, make_document, make_extraction


def test_prompt_contains_block_ids_and_text():
    document = make_document("t(28) = 2.10")
    prompt = build_prompt(document)
    assert "[p1b1] t(28) = 2.10" in prompt
    assert "$document" not in prompt


def test_run_validates_llm_output():
    expected = make_extraction([])
    llm = FakeLLM(expected.model_dump(mode="json"))
    result = extract.run(make_document("text"), llm)
    assert isinstance(result, Extraction)
    assert result == expected
    assert len(llm.calls) == 1


def test_fingerprint_is_stable():
    assert extract.prompt_fingerprint() == extract.prompt_fingerprint()
