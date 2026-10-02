"""Recompute p from the reported statistic and degrees of freedom.

Same idea as statcheck (Nuijten et al., 2016): a reported p is consistent if
it matches some p obtainable from a statistic that rounds to the printed one.

Context the paper states is respected. An adjusted p (Tukey, Bonferroni, ...)
cannot be recomputed from the unadjusted statistic, so it is reported as info
instead of an inconsistency. A test stated to be one-tailed is checked against
the one-tailed p. Without these, most false alarms in an audit of 22 real
papers came from exactly these two cases.
"""

import math

from scipy import stats

from paper_stat_critic.model import (
    Document,
    Extraction,
    Finding,
    PComparator,
    ReportedTest,
    Severity,
    StatisticKind,
)

NAME = "pvalue_recompute"
ALPHA = 0.05
_TWO_TAILED_KINDS = {StatisticKind.T, StatisticKind.Z, StatisticKind.R}


def parse_number(text: str) -> float:
    # Papers print U+2212 (minus sign) where Python expects "-".
    cleaned = text.strip().replace("−", "-")
    return float(cleaned)


def decimals(text: str) -> int:
    _, _, fraction = text.strip().partition(".")
    return len(fraction)


def p_from_statistic(
    kind: StatisticKind, value: float, df1: float | None, df2: float | None
) -> float:
    """p as the paper would compute it: two-tailed for t, z, r; upper tail for F, chi2."""
    if kind is StatisticKind.T:
        return 2 * stats.t.sf(abs(value), df1)
    if kind is StatisticKind.Z:
        return 2 * stats.norm.sf(abs(value))
    if kind is StatisticKind.R:
        # r converts to t with n-2 df; |r| is capped just below 1 because the
        # conversion divides by 1 - r^2.
        r = min(abs(value), 1 - 1e-12)
        t_value = r * math.sqrt(df1 / (1 - r * r))
        return 2 * stats.t.sf(t_value, df1)
    if kind is StatisticKind.F:
        return stats.f.sf(value, df1, df2)
    if kind is StatisticKind.CHI2:
        return stats.chi2.sf(value, df1)
    raise ValueError(f"unsupported statistic kind: {kind}")


def p_range(test: ReportedTest) -> tuple[float, float]:
    """Smallest and largest p from any statistic that rounds to the printed value."""
    value = abs(parse_number(test.statistic))
    half_unit = 0.5 * 10 ** -decimals(test.statistic)
    low_stat = max(value - half_unit, 0.0)
    high_stat = value + half_unit
    # Larger statistics always give smaller p for every supported kind, so the
    # upper end of the statistic gives the lower end of p.
    p_low = p_from_statistic(test.kind, high_stat, test.df1, test.df2)
    p_high = p_from_statistic(test.kind, low_stat, test.df1, test.df2)
    return p_low, p_high


def is_consistent(comparator: PComparator, p_text: str, p_low: float, p_high: float) -> bool:
    reported = parse_number(p_text)
    if comparator is PComparator.LT:
        return p_low < reported
    if comparator is PComparator.GT:
        return p_high > reported
    half_unit = 0.5 * 10 ** -decimals(p_text)
    overlaps_from_below = p_low <= reported + half_unit
    overlaps_from_above = p_high >= reported - half_unit
    return overlaps_from_below and overlaps_from_above


def reported_significant(comparator: PComparator, p_text: str) -> bool:
    reported = parse_number(p_text)
    if comparator is PComparator.LT:
        return reported <= ALPHA
    if comparator is PComparator.EQ:
        return reported < ALPHA
    return False


def _checkable(test: ReportedTest) -> bool:
    if test.kind is StatisticKind.OTHER:
        return False
    if test.p_comparator is None or test.p_value is None:
        return False
    if test.kind is not StatisticKind.Z and test.df1 is None:
        return False
    if test.kind is StatisticKind.F and test.df2 is None:
        return False
    return True


def _format_df(test: ReportedTest) -> str:
    if test.kind is StatisticKind.Z:
        return ""
    if test.kind is StatisticKind.F:
        return f"({test.df1:g}, {test.df2:g})"
    return f"({test.df1:g})"


def _adjusted_note(test: ReportedTest) -> Finding:
    return Finding(
        check=NAME,
        severity=Severity.INFO,
        title=f"{test.id}: adjusted p not recomputed",
        detail="The paper reports this p as adjusted for multiple comparisons; "
        "it cannot be recomputed from the unadjusted statistic.",
        test_ids=[test.id],
        evidence=[test.evidence],
    )


def _finding_for(test: ReportedTest) -> Finding | None:
    if test.p_adjusted:
        return _adjusted_note(test)

    p_low, p_high = p_range(test)
    # A stated one-tailed test is judged on the one-tailed p; the "matches
    # only one-tailed" hint below is then meaningless and is skipped.
    one_tailed = test.one_tailed and test.kind in _TWO_TAILED_KINDS
    if one_tailed:
        p_low, p_high = p_low / 2, p_high / 2
    if is_consistent(test.p_comparator, test.p_value, p_low, p_high):
        return None

    printed = parse_number(test.statistic)
    computed = p_from_statistic(test.kind, printed, test.df1, test.df2)
    if one_tailed:
        computed = computed / 2
    reported_text = f"{test.kind.value}{_format_df(test)} = {test.statistic}, "
    reported_text += f"p {test.p_comparator.value} {test.p_value}"
    tail_note = " (one-tailed, as stated)" if one_tailed else ""
    detail = f"Reported {reported_text}; recomputed p{tail_note} = {computed:.4f}."

    one_tailed_ok = False
    if test.kind in _TWO_TAILED_KINDS and not one_tailed:
        one_tailed_ok = is_consistent(test.p_comparator, test.p_value, p_low / 2, p_high / 2)

    if one_tailed_ok:
        severity = Severity.LOW
        title = f"{test.id}: p matches only a one-tailed test"
        detail += " Consistent if the test was one-tailed; check whether that was stated."
    elif reported_significant(test.p_comparator, test.p_value) != (computed < ALPHA):
        severity = Severity.HIGH
        title = f"{test.id}: p inconsistent and the significance decision flips"
        detail += f" At alpha = {ALPHA} the reported and recomputed conclusions differ."
    else:
        severity = Severity.MEDIUM
        title = f"{test.id}: p inconsistent with statistic and df"

    return Finding(
        check=NAME,
        severity=severity,
        title=title,
        detail=detail,
        test_ids=[test.id],
        evidence=[test.evidence],
    )


def check(extraction: Extraction, document: Document) -> list[Finding]:
    findings: list[Finding] = []
    for test in extraction.tests:
        if not _checkable(test):
            continue
        try:
            finding = _finding_for(test)
        except ValueError:
            # A statistic or p the LLM copied in a form we cannot parse
            # (e.g. "2.1a") is skipped rather than reported as an error in
            # the paper; quote_anchor already covers bad extraction.
            continue
        if finding is not None:
            findings.append(finding)
    return findings
