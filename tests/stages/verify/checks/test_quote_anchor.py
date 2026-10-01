from paper_stat_critic.model import StatisticKind
from paper_stat_critic.stages.verify.checks import quote_anchor
from tests.conftest import make_document, make_extraction, make_test


def test_compact_ignores_layout_differences():
    pdf_text = "a signiﬁcant effect, t(28) = −2.10, p = .045"
    llm_text = "A significant effect, t(28) = -2.10, p = .045"
    assert quote_anchor.compact(pdf_text) == quote_anchor.compact(llm_text)


def test_quote_present_passes():
    document = make_document("We found a signi-ficant effect, t(28) = 2.10, p = .045.")
    test = make_test(StatisticKind.T, "2.10", ".045", df1=28, quote="significant effect, t(28)")
    assert quote_anchor.check(make_extraction([test]), document) == []


def test_missing_quote_is_flagged():
    document = make_document("Nothing relevant here.")
    test = make_test(StatisticKind.T, "2.10", ".045", df1=28, quote="t(28) = 2.10")
    [finding] = quote_anchor.check(make_extraction([test]), document)
    assert finding.test_ids == ["T1"]
