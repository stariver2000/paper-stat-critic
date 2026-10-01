"""A parsed paper: ordered text blocks with stable ids for citation."""

from pydantic import BaseModel


class Block(BaseModel):
    """A paragraph-sized chunk of text.

    `id` is what the LLM cites in Evidence.block_id, so it must stay stable
    for the same PDF across runs.
    """

    id: str
    page: int
    text: str


class Document(BaseModel):
    paper_id: str
    blocks: list[Block]

    def full_text(self) -> str:
        texts = [block.text for block in self.blocks]
        return "\n".join(texts)
