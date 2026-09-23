"""Parser cho tài liệu PDF (catalogue, manual, bulletin, poster...).

Mọi parser trong ``parsers/`` trả về cùng một schema dict (JSON-serializable)
để ``pipeline.py`` ghi thẳng vào ``data/cleaned_json/``:

    {
      "doc_id": "level_1/ac-compressor-leaflet",
      "source_path": "data/raw/level_1/ac-compressor-leaflet.pdf",
      "level": "level_1",
      "doc_type": "pdf",
      "language": "en",              # do utils/lang_detector.py điền
      "text": "toàn bộ văn bản đã nối",
      "blocks": [                    # đơn vị nhỏ nhất để chunk/embedding
        {"index": 0, "text": "...", "metadata": {"page": 1}}
      ],
      "metadata": {"page_count": 12, "needs_ocr": false, "engine": "..."}
    }

TODO: cài dependency (pypdf/pdfplumber, pytesseract nếu là PDF scan) rồi
implement ``parse_pdf``; giữ nguyên signature để không phải sửa pipeline.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

SUPPORTED_SUFFIXES = {".pdf"}
DOC_TYPE = "pdf"


def parse_pdf(path: str | Path, *, level: str | None = None) -> Dict[str, Any]:
    """Trích xuất text + metadata của 1 file PDF thành dict theo schema ở trên.

    Args:
        path: đường dẫn tới file ``.pdf``.
        level: tên nhóm dữ liệu (``level_1``/``level_2``/``level_3``) để gắn vào doc.

    Raises:
        FileNotFoundError: nếu ``path`` không tồn tại.
        ValueError: nếu file không phải PDF.
        NotImplementedError: chưa implement engine trích xuất.
    """
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"Không tìm thấy file PDF: {source}")
    if source.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise ValueError(f"{source.name} không phải file PDF")

    raise NotImplementedError(
        "TODO: implement extract PDF (text layer + OCR fallback) trong parsers/pdf_parser.py"
    )


def parse(path: str | Path, *, level: str | None = None) -> Dict[str, Any]:
    """Entry point thống nhất cho pipeline."""
    return parse_pdf(path, level=level)


def blocks_to_text(blocks: List[Dict[str, Any]], *, separator: str = "\n\n") -> str:
    """Ghép ``blocks`` thành ``text`` phẳng (giữ 1 chỗ để đổi cách ghép sau này)."""
    return separator.join(block.get("text", "") for block in blocks)
