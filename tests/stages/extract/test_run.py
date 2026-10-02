from paper_stat_critic.model import Block, Document, Extraction, StatisticKind
from paper_stat_critic.stages import extract
from paper_stat_critic.stages.extract.run import build_prompt, chunk_blocks, merge_tests
from tests.conftest import FakeLLM, make_document, make_extraction, make_test


def blocks_of(sizes: list[int]) -> list[Block]:
    return [Block(id=f"p1b{i}", page=1, text="x" * size) for i, size in enumerate(sizes, start=1)]


def test_prompt_contains_block_ids_and_text():
    document = make_document("t(28) = 2.10")
    prompt = build_prompt("prompt_tests.md", document.blocks)
    assert "[p1b1] t(28) = 2.10" in prompt
    assert "$document" not in prompt


def test_chunks_respect_limit_and_keep_order():
    chunks = chunk_blocks(blocks_of([40, 40, 40, 90, 10]), chunk_chars=100)
    sizes = [[len(block.text) for block in chunk] for chunk in chunks]
    assert sizes == [[40, 40], [40], [90, 10]]


def test_oversized_block_is_its_own_chunk():
    chunks = chunk_blocks(blocks_of([10, 500, 10]), chunk_chars=100)
    assert [len(chunk) for chunk in chunks] == [1, 1, 1]


def test_merge_drops_exact_repeats_and_renumbers():
    first = make_test(StatisticKind.T, "2.10", ".045", df1=28, test_id="T1")
    second = make_test(StatisticKind.F, "4.41", ".045", df1=1, df2=28, test_id="T1")
    merged = merge_tests([[first], [first, second]])
    assert [test.id for test in merged] == ["T1", "T2"]
    assert [test.kind for test in merged] == [StatisticKind.T, StatisticKind.F]


def test_run_calls_design_once_and_tests_per_chunk():
    test = make_test(StatisticKind.T, "2.10", ".045", df1=28)
    expected = make_extraction([test])
    llm = FakeLLM(expected.model_dump(mode="json"))
    document = Document(paper_id="p", blocks=blocks_of([60, 60, 60]))
    result = extract.run(document, llm, chunk_chars=100, workers=2)
    assert isinstance(result, Extraction)
    assert len(llm.calls) == 1 + 3
    # Every chunk returned the same test; it must appear once.
    assert len(result.tests) == 1


def test_fingerprint_depends_on_chunk_size():
    assert extract.prompt_fingerprint(100) == extract.prompt_fingerprint(100)
    assert extract.prompt_fingerprint(100) != extract.prompt_fingerprint(200)
