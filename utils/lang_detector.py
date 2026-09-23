"""Phát hiện ngôn ngữ cho text/transcript trước khi đưa vào cleaned_json.

Thiết kế: nếu có ``langdetect`` (hoặc ``pycld3``) thì dùng, còn không thì
fallback heuristic dựa trên bảng chữ cái + dấu tiếng Việt (chỉ standard library).
Nhờ vậy module luôn chạy được ở môi trường chưa cài dependency.

TODO: khi chốt thư viện, bổ sung vào requirements.txt và giữ nguyên signature
``detect_language(text) -> str`` để pipeline không phải sửa.
"""

from __future__ import annotations

import re
from typing import Dict, Optional

SUPPORTED_LANGS = ("vi", "en", "ja", "ko", "zh", "th", "unknown")
DEFAULT_LANG = "unknown"

# Heuristic: dấu đặc trưng tiếng Việt (Latin + combining marks).
_VI_DIACRITIC_RE = re.compile(
    r"[ăâđêôơưĂÂĐÊÔƠƯ"
    r"áàảãạắằẳẵặấầẩẫậéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ"
    r"ÁÀẢÃẠẮẰẲẴẶẤẦẨẪẬÉÈẺẼẸẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌỐỒỔỖỘỚỜỞỠỢÚÙỦŨỤỨỪỬỮỰÝỲỶỸỴ]"
)

_RANGES = {
    "ja": ((0x3040, 0x30FF), (0x31F0, 0x31FF)),  # Hiragana + Katakana
    "ko": ((0xAC00, 0xD7AF), (0x1100, 0x11FF)),  # Hangul
    "zh": ((0x4E00, 0x9FFF),),                   # CJK Unified Ideographs
    "th": ((0x0E00, 0x0E7F),),                   # Thai
}


def _count_chars(text: str) -> Dict[str, int]:
    """Đếm số ký tự thuộc từng nhóm chữ viết (dùng cho heuristic)."""
    counts: Dict[str, int] = {"ja": 0, "ko": 0, "zh": 0, "th": 0, "latin": 0, "vi_mark": 0}
    for char in text:
        code = ord(char)
        for lang, ranges in _RANGES.items():
            if any(start <= code <= end for start, end in ranges):
                counts[lang] += 1
                break
        else:
            if _VI_DIACRITIC_RE.match(char):
                counts["vi_mark"] += 1
                counts["latin"] += 1
            elif char.isascii() and char.isalpha():
                counts["latin"] += 1
    return counts


def detect_language(text: str, default: str = DEFAULT_LANG) -> str:
    """Trả về mã ngôn ngữ ISO 639-1 ngắn gọn (``vi``/``en``/``ja``/...).

    Args:
        text: văn bản đã clean (nên gọi ``text_cleaner.clean_text`` trước).
        default: giá trị trả về khi không đủ dữ liệu để kết luận.

    Returns:
        Mã ngôn ngữ hoặc ``default`` nếu text rỗng/không nhận dạng được.
    """
    if not text or not text.strip():
        return default

    try:  # pragma: no cover - chỉ chạy khi môi trường có langdetect
        from langdetect import detect  # type: ignore

        return detect(text)
    except Exception:
        return _detect_by_heuristic(text, default=default)


def _detect_by_heuristic(text: str, *, default: str = DEFAULT_LANG) -> str:
    """Fallback không cần dependency: ưu tiên chữ viết CJK/Thai rồi tới Latin."""
    counts = _count_chars(text)
    for lang in ("ja", "ko", "th", "zh"):
        if counts[lang] >= 5:
            return lang

    latin = counts["latin"]
    if latin >= 10:
        return "vi" if counts["vi_mark"] / latin >= 0.02 else "en"
    return default


def is_vietnamese(text: str) -> bool:
    """Tiện ích nhanh cho các bước cần lọc riêng tài liệu tiếng Việt."""
    return detect_language(text) == "vi"


def detect_languages(texts: Optional[list]) -> Dict[str, int]:
    """Thống kê phân bố ngôn ngữ của nhiều khối text (dùng để log/report)."""
    summary: Dict[str, int] = {}
    for text in texts or []:
        lang = detect_language(text)
        summary[lang] = summary.get(lang, 0) + 1
    return summary
