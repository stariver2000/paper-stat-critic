from paper_stat_critic.stages import ingest
from tests.conftest import FakeParser


def test_blocks_get_page_scoped_ids():
    parser = FakeParser(["first para\n\nsecond para", "third para"])
    document = ingest.run(b"", "paper", parser)
    ids = [block.id for block in document.blocks]
    assert ids == ["p1b1", "p1b2", "p2b1"]


def test_lines_are_joined_and_hyphens_kept():
    parser = FakeParser(["a within-\nsubjects design\nwas used"])
    [block] = ingest.run(b"", "paper", parser).blocks
    assert block.text == "a within-subjects design was used"


def test_ligatures_are_normalized():
    parser = FakeParser(["signiﬁcant"])
    [block] = ingest.run(b"", "paper", parser).blocks
    assert block.text == "significant"


def test_long_text_splits_at_sentence_end():
    sentence = "This sentence is about forty characters. "
    parser = FakeParser(["\n".join([sentence] * 20)])
    blocks = ingest.run(b"", "paper", parser).blocks
    assert len(blocks) > 1
    assert all(block.text.endswith(".") for block in blocks)


def test_pdfium_line_hyphen_marker_becomes_hyphen():
    parser = FakeParser(["a within\ufffe\nsubject design"])
    [block] = ingest.run(b"", "paper", parser).blocks
    assert block.text == "a within-subject design"
