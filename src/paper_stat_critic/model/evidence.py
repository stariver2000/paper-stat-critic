"""Where in the paper a claim comes from."""

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    quote: str = Field(description="Verbatim span copied from the paper, 5-40 words.")
    block_id: str | None = Field(description="Id of the block the quote was copied from.")
