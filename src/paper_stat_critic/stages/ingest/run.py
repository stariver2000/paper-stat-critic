"""ingest: PDF bytes -> Document of citable blocks."""

import unicodedata

from paper_stat_critic.model import Block, Document
from paper_stat_critic.ports import PageText, PdfParser

# A block closes at the first sentence end after this many characters. Short
# enough that a block id pins a quote down, long enough that a reported test
# and its sentence usually stay together.
MIN_BLOCK_CHARS = 400
_SENTENCE_ENDINGS = (".", "?", "!", ":")


# pdfium marks a hyphen it found at a line break with U+FFFE instead of "-".
_PDFIUM_LINE_HYPHEN = "\ufffe"


def _clean_lines(page_text: str) -> list[str]:
    # NFKC turns ligatures such as "ﬁ" into "fi", so quotes the LLM types
    # back can match the source text.
    normalized = unicodedata.normalize("NFKC", page_text)
    normalized = normalized.replace(_PDFIUM_LINE_HYPHEN, "-")
    lines = normalized.splitlines()
    return [line.strip() for line in lines]


def _join(current: str, line: str) -> str:
    if not current:
        return line
    # A line ending in "-" is either a word split across lines ("statis-tical")
    # or a real compound ("within-subjects"). Keeping the hyphen and adding
    # no space is readable in both cases and loses nothing.
    if current.endswith("-"):
        return current + line
    return current + " " + line


def _blocks_of_page(page: PageText) -> list[str]:
    blocks: list[str] = []
    current = ""
    for line in _clean_lines(page.text):
        if not line:
            if current:
                blocks.append(current)
            current = ""
            continue
        current = _join(current, line)
        long_enough = len(current) >= MIN_BLOCK_CHARS
        if long_enough and current.endswith(_SENTENCE_ENDINGS):
            blocks.append(current)
            current = ""
    if current:
        blocks.append(current)
    return blocks


def run(pdf: bytes, paper_id: str, parser: PdfParser) -> Document:
    blocks: list[Block] = []
    for page in parser.parse(pdf):
        page_blocks = _blocks_of_page(page)
        for index, text in enumerate(page_blocks, start=1):
            block_id = f"p{page.page}b{index}"
            blocks.append(Block(id=block_id, page=page.page, text=text))
    return Document(paper_id=paper_id, blocks=blocks)
