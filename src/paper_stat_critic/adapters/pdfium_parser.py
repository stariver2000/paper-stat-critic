"""PdfParser backed by pypdfium2.

pypdfium2 is Apache-2.0/BSD licensed, which keeps this MIT project free of
copyleft dependencies (PyMuPDF would pull in AGPL).
"""

import pypdfium2 as pdfium

from paper_stat_critic.ports import PageText


class PdfiumParser:
    def parse(self, pdf: bytes) -> list[PageText]:
        document = pdfium.PdfDocument(pdf)
        pages: list[PageText] = []
        try:
            for index in range(len(document)):
                textpage = document[index].get_textpage()
                # pdfium returns text in content-stream order, which follows
                # columns for typical LaTeX two-column papers. Sorting by
                # coordinates would interleave the two columns line by line.
                text = textpage.get_text_range()
                pages.append(PageText(page=index + 1, text=text))
        finally:
            document.close()
        return pages
