"""Parser cho bảng tính Excel/CSV (catalogue dạng bảng, spec, giá...).

Trả về cùng schema dict với ``parsers/pdf_parser.py``, trong đó ``blocks``
tương ứng từng dòng đã stringify để có thể chunk/embedding sau này.

TODO: cài openpyxl/pandas rồi implement ``parse_excel``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

SUPPORTED_SUFFIXES = {".xlsx", ".xlsm", ".xls", ".csv"}
DOC_TYPE = "excel"


def parse_excel(
    path: str | Path,
    *,
    level: str | None = None,
    sheet_names: List[str] | None = None,
) -> Dict[str, Any]:
    """Đọc 1 workbook/tệp CSV thành dict theo schema chung.

    Args:
        path: đường dẫn file bảng tính.
        level: tên nhóm dữ liệu (``level_1``/``level_2``/``level_3``).
        sheet_names: chỉ đọc các sheet này; ``None`` = đọc tất cả.

    Raises:
        FileNotFoundError: nếu ``path`` không tồn tại.
        ValueError: nếu định dạng không được hỗ trợ.
        NotImplementedError: chưa implement engine đọc bảng.
    """
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"Không tìm thấy file bảng tính: {source}")
    if source.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise ValueError(f"{source.name} không phải định dạng bảng tính được hỗ trợ")

    raise NotImplementedError(
        "TODO: implement đọc Excel/CSV (openpyxl/pandas) trong parsers/excel_parser.py"
    )


def parse(
    path: str | Path,
    *,
    level: str | None = None,
    sheet_names: List[str] | None = None,
) -> Dict[str, Any]:
    """Entry point thống nhất cho pipeline."""
    return parse_excel(path, level=level, sheet_names=sheet_names)


def rows_to_blocks(rows: List[Dict[str, Any]], *, sheet: str | None = None) -> List[Dict[str, Any]]:
    """Chuyển list row (dict cột -> giá trị) thành list ``blocks`` chuẩn của pipeline."""
    blocks: List[Dict[str, Any]] = []
    for index, row in enumerate(rows):
        text = " | ".join(f"{key}: {value}" for key, value in row.items() if value not in (None, ""))
        blocks.append({"index": index, "text": text, "metadata": {"sheet": sheet, "row": index + 1}})
    return blocks
