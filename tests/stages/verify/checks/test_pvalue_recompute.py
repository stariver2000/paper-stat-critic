import pytest

from paper_stat_critic.model import PComparator, Severity, StatisticKind
from paper_stat_critic.stages.verify.checks import pvalue_recompute
from tests.conftest import make_document, make_extraction, make_test

DOC = make_document("")


def run_one(test):
    return pvalue_recompute.check(make_extraction([test]), DOC)


@pytest.mark.parametrize(
    ("kind", "statistic", "df1", "df2", "p_value"),
    [
        (StatisticKind.T, "2.10", 28, None, ".045"),  # p = .0449
        (StatisticKind.T, "-2.10", 28, None, ".045"),  # sign does not matter
        (StatisticKind.F, "4.41", 1, 28, ".045"),  # F = t^2
        (StatisticKind.CHI2, "3.84", 1, None, ".05"),
        (StatisticKind.Z, "1.96", None, None, ".05"),
        (StatisticKind.R, ".37", 28, None, ".045"),
    ],
)
def test_consistent_reports_pass(kind, statistic, df1, df2, p_value):
    test = make_test(kind, statistic, p_value, df1=df1, df2=df2)
    assert run_one(test) == []


def test_rounding_of_statistic_is_tolerated():
    # t(28) = 2.1 covers 2.05..2.15, i.e. p from .041 to .050.
    test = make_test(StatisticKind.T, "2.1", ".049", df1=28)
    assert run_one(test) == []


def test_inconsistent_without_decision_change_is_medium():
    test = make_test(StatisticKind.T, "2.10", ".030", df1=28)
    [finding] = run_one(test)
    assert finding.severity is Severity.MEDIUM
    assert finding.test_ids == ["T1"]


def test_decision_flip_is_high():
    # t(28) = 1.80 gives p = .083 (one-tailed .041), reported as p = .02.
    test = make_test(StatisticKind.T, "1.80", ".02", df1=28)
    [finding] = run_one(test)
    assert finding.severity is Severity.HIGH


def test_one_tailed_match_is_low():
    # Two-tailed p = .083; one-tailed p = .041.
    test = make_test(StatisticKind.T, "1.80", ".041", df1=28)
    [finding] = run_one(test)
    assert finding.severity is Severity.LOW


def test_less_than_comparator():
    ok = make_test(StatisticKind.T, "5.00", ".001", df1=28, comparator=PComparator.LT)
    bad = make_test(StatisticKind.T, "2.10", ".01", df1=28, comparator=PComparator.LT)
    assert run_one(ok) == []
    assert len(run_one(bad)) == 1


def test_unicode_minus_is_parsed():
    test = make_test(StatisticKind.T, "−2.10", ".045", df1=28)
    assert run_one(test) == []


@pytest.mark.parametrize(
    "test",
    [
        make_test(StatisticKind.OTHER, "12", ".01"),
        make_test(StatisticKind.T, "2.10", ".045", df1=None),
        make_test(StatisticKind.F, "4.41", ".045", df1=1, df2=None),
        make_test(StatisticKind.T, "2.1a", ".045", df1=28),
    ],
)
def test_uncheckable_tests_are_skipped(test):
    assert run_one(test) == []
