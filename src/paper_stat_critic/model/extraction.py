"""What the extract stage pulls out of a paper.

The field descriptions double as instructions to the LLM: the JSON Schema
generated from these models is passed to it verbatim, so wording here
directly affects extraction quality.
"""

from enum import StrEnum

from pydantic import BaseModel, Field

from paper_stat_critic.model.evidence import Evidence


class StatisticKind(StrEnum):
    T = "t"
    F = "F"
    CHI2 = "chi2"
    R = "r"
    Z = "z"
    OTHER = "other"


class PComparator(StrEnum):
    EQ = "="
    LT = "<"
    GT = ">"


class Assignment(StrEnum):
    WITHIN = "within"
    BETWEEN = "between"
    UNCLEAR = "unclear"


class MeasureScale(StrEnum):
    SINGLE_ITEM_ORDINAL = "single_item_ordinal"
    MULTI_ITEM_SCALE = "multi_item_scale"
    CONTINUOUS = "continuous"
    COUNT = "count"
    BINARY = "binary"
    UNCLEAR = "unclear"


class ReportedTest(BaseModel):
    id: str = Field(description="T1, T2, ... in order of appearance.")
    analysis: str = Field(description="Test name as the authors call it, e.g. 'paired t-test'.")
    kind: StatisticKind
    df1: float | None = Field(description="First degrees of freedom; null if not printed.")
    df2: float | None = Field(description="Second degrees of freedom (F only); else null.")
    statistic: str = Field(description="Test statistic exactly as printed, e.g. '-2.10'.")
    p_comparator: PComparator | None = Field(description="Relation printed before p.")
    p_value: str | None = Field(description="p exactly as printed, e.g. '.045'.")
    p_adjusted: bool = Field(
        description=(
            "True only if the paper says this p is corrected for multiple comparisons or comes "
            "from a post-hoc procedure that adjusts p (e.g. Tukey HSD, Bonferroni, Holm, FDR, "
            "Sidak, Scheffe, Games-Howell)."
        )
    )
    one_tailed: bool = Field(
        description="True only if the paper says the test was one-tailed, one-sided or directional."
    )
    evidence: Evidence


# Factor, StudyDesign and Measure are not checked by the verify stage. They are
# extracted now because the planned assess stage (docs/DESIGN.md, "Roadmap")
# matches rubric rules against them, and a reader of 02_extraction.json
# already uses them to see the design at a glance.


class Factor(BaseModel):
    name: str
    levels: list[str]
    assignment: Assignment = Field(description="within = every participant experiences all levels.")


class StudyDesign(BaseModel):
    n_participants: int | None = Field(description="Participants in the analysed sample.")
    factors: list[Factor]
    multiple_trials_per_condition: bool | None = Field(
        description="True if a participant contributes several observations per condition."
    )
    evidence: list[Evidence]


class Measure(BaseModel):
    name: str
    scale: MeasureScale
    evidence: Evidence


class Extraction(BaseModel):
    design: StudyDesign
    measures: list[Measure]
    tests: list[ReportedTest]
