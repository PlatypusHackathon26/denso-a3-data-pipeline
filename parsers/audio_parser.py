"""Parser cho file audio (ghi âm phỏng vấn, hotline, training...).

Audio được chuyển thành transcript rồi cắt thành ``blocks`` theo segment của
ASR (kèm ``start``/``end`` giây để truy vết) — cùng schema với các parser khác.

TODO: cài faster-whisper (hoặc engine ASR khác) rồi implement ``parse_audio``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

SUPPORTED_SUFFIXES = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".wma"}
DOC_TYPE = "audio"


def parse_audio(
    path: str | Path,
    *,
    level: str | None = None,
    language: str | None = None,
) -> Dict[str, Any]:
    """Transcribe 1 file audio thành dict theo schema chung.

    Args:
        path: đường dẫn file audio.
        level: tên nhóm dữ liệu (``level_1``/``level_2``/``level_3``).
        language: mã ngôn ngữ gợi ý cho ASR (``vi``/``en``/...); ``None`` = tự nhận.

    Raises:
        FileNotFoundError: nếu ``path`` không tồn tại.
        ValueError: nếu định dạng không được hỗ trợ.
        NotImplementedError: chưa implement engine ASR.
    """
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"Không tìm thấy file audio: {source}")
    if source.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise ValueError(f"{source.name} không phải định dạng audio được hỗ trợ")

    raise NotImplementedError(
        "TODO: implement transcribe (faster-whisper) trong parsers/audio_parser.py"
    )


def parse(
    path: str | Path,
    *,
    level: str | None = None,
    language: str | None = None,
) -> Dict[str, Any]:
    """Entry point thống nhất cho pipeline."""
    return parse_audio(path, level=level, language=language)


def segments_to_blocks(segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Chuyển segment ASR (``{"start":..,"end":..,"text":..}``) thành ``blocks`` chuẩn."""
    blocks: List[Dict[str, Any]] = []
    for index, segment in enumerate(segments):
        blocks.append(
            {
                "index": index,
                "text": segment.get("text", ""),
                "metadata": {"start": segment.get("start"), "end": segment.get("end")},
            }
        )
    return blocks
