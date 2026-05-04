"""
Parser de documentos PDF financeiros usando pdfplumber.
"""
from __future__ import annotations

import pdfplumber


def extract_pdf(file: str) -> str:
    """
    Extrai todo o texto de um arquivo PDF página a página.

    Args:
        file: Caminho local para o arquivo PDF.

    Returns:
        Texto concatenado de todas as páginas.

    Raises:
        FileNotFoundError: Se o arquivo não existir.
        ValueError: Se o PDF estiver corrompido ou sem texto extraível.
    """
    text_parts: list[str] = []

    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

    if not text_parts:
        raise ValueError(f"Nenhum texto extraível encontrado em: {file}")

    return "\n".join(text_parts)
