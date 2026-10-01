"""Stage order and the artifact file each stage writes.

The numbered file names make the flow visible in runs/<paper_id>/.
"""

from enum import StrEnum


class StageName(StrEnum):
    INGEST = "ingest"
    EXTRACT = "extract"
    VERIFY = "verify"


STAGE_ORDER: list[StageName] = [StageName.INGEST, StageName.EXTRACT, StageName.VERIFY]

ARTIFACT_FILES: dict[StageName, str] = {
    StageName.INGEST: "01_document.json",
    StageName.EXTRACT: "02_extraction.json",
    StageName.VERIFY: "03_verify.json",
}


def stages_until(last: StageName) -> list[StageName]:
    end = STAGE_ORDER.index(last) + 1
    return STAGE_ORDER[:end]
