"""Entry point của pipeline denso-a3: raw (level_1/2/3) -> cleaned_json.

Cấu trúc thư mục mà pipeline giả định (đã có sẵn trong repo):

    data/
      raw/
        level_1/   <- tài liệu nhóm 1 (vd: catalogue, manual)
        level_2/   <- tài liệu nhóm 2
        level_3/   <- tài liệu nhóm 3
      cleaned_json/ <- output: mỗi tài liệu 1 file .json theo schema của parsers/
    utils/          <- text_cleaner.py, lang_detector.py
    parsers/        <- pdf_parser.py, excel_parser.py, audio_parser.py

Cách dùng:

    python pipeline.py                      # liệt kê file raw tìm thấy
    python pipeline.py --write-manifest     # + ghi data/cleaned_json/_manifest.json
    python pipeline.py --process            # chạy thử stage parse/clean/detect
    python pipeline.py --levels level_1 level_3 --limit 5

Lưu ý: các stage ``parse`` trong ``parsers/*`` hiện là skeleton
(``NotImplementedError``), nên ``--process`` sẽ báo rõ file nào còn chờ implement
thay vì crash cả pipeline.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
CLEANED_DIR = DATA_DIR / "cleaned_json"
MANIFEST_FILENAME = "_manifest.json"

LEVELS: tuple[str, ...] = ("level_1", "level_2", "level_3")

# suffix -> (doc_type, tên module parser trong parsers/)
ROUTING: Dict[str, tuple] = {}
for _suffix in (".pdf",):
    ROUTING[_suffix] = ("pdf", "pdf_parser")
for _suffix in (".xlsx", ".xlsm", ".xls", ".csv"):
    ROUTING[_suffix] = ("excel", "excel_parser")
for _suffix in (".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".wma"):
    ROUTING[_suffix] = ("audio", "audio_parser")

SKIP_FILENAMES = {".gitkeep"}


def _is_ignored(path: Path) -> bool:
    """Bỏ qua file rác của hệ điều hành/editor và file ẩn của git."""
    return path.name in SKIP_FILENAMES or path.name.startswith("~$") or path.name.startswith(".")


def discover_raw_files(levels: Sequence[str] = LEVELS) -> List[Dict[str, Any]]:
    """Liệt kê mọi file trong ``data/raw/<level>`` kèm doc_type suy ra từ đuôi file."""
    found: List[Dict[str, Any]] = []
    for level in levels:
        level_dir = RAW_DIR / level
        if not level_dir.is_dir():
            print(f"[warn] không thấy thư mục: {level_dir}", file=sys.stderr)
            continue

        for path in sorted(level_dir.rglob("*")):
            if not path.is_file() or _is_ignored(path):
                continue

            doc_type, parser_module = ROUTING.get(path.suffix.lower(), ("unknown", None))
            found.append(
                {
                    "level": level,
                    "path": path,
                    "rel_path": path.relative_to(PROJECT_ROOT).as_posix(),
                    "doc_type": doc_type,
                    "parser_module": parser_module,
                    "size_bytes": path.stat().st_size,
                }
            )
    return found


def doc_id_for(record: Dict[str, Any]) -> str:
    """ID ổn định cho 1 tài liệu: ``<level>/<tên file không đuôi>`` (đã slug hoá)."""
    stem = Path(record["path"]).stem.strip().lower()
    slug = "".join(char if char.isalnum() else "-" for char in stem)
    return f"{record['level']}/{(slug.strip('-') or 'doc')}"


def build_manifest(records: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """Tạo manifest JSON mô tả các file raw đã phát hiện (để đối chiếu tiến độ)."""
    entries: List[Dict[str, Any]] = []
    for record in records:
        entries.append(
            {
                "doc_id": doc_id_for(record),
                "level": record["level"],
                "rel_path": record["rel_path"],
                "doc_type": record["doc_type"],
                "parser_module": record["parser_module"],
                "size_bytes": record["size_bytes"],
            }
        )

    return {
        "project": PROJECT_ROOT.name,
        "raw_dir": RAW_DIR.relative_to(PROJECT_ROOT).as_posix(),
        "cleaned_dir": CLEANED_DIR.relative_to(PROJECT_ROOT).as_posix(),
        "levels": list(LEVELS),
        "total_files": len(entries),
        "files": entries,
    }


def write_manifest(manifest: Dict[str, Any], output_path: Path | None = None) -> Path:
    """Ghi manifest xuống ``data/cleaned_json/_manifest.json`` (tạo thư mục nếu thiếu)."""
    destination = output_path or (CLEANED_DIR / MANIFEST_FILENAME)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return destination


def process_records(records: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Chạy thử stage parse -> clean -> detect lang cho từng file.

    Trả về danh sách kết quả; file nào có parser chưa implement thì đánh dấu
    ``status="pending"`` kèm lý do, không làm chết cả pipeline.
    """
    from utils import lang_detector, text_cleaner

    results: List[Dict[str, Any]] = []
    for record in records:
        module_name = record["parser_module"]
        if module_name is None:
            results.append(
                {
                    "doc_id": doc_id_for(record),
                    "status": "unsupported",
                    "reason": f"đuôi file chưa hỗ trợ: {Path(record['path']).suffix}",
                }
            )
            continue

        try:
            parser = __import__(f"parsers.{module_name}", fromlist=[module_name])
            parsed = parser.parse(record["path"], level=record["level"])
        except NotImplementedError as error:
            results.append({"doc_id": doc_id_for(record), "status": "pending", "reason": str(error)})
            continue
        except Exception as error:  # pragma: no cover - lỗi thật khi parser đã implement
            results.append({"doc_id": doc_id_for(record), "status": "error", "reason": repr(error)})
            continue

        blocks = [
            text_cleaner.clean_text(block.get("text", "")) for block in parsed.get("blocks", [])
        ]
        text = text_cleaner.clean_text(parsed.get("text", ""))
        results.append(
            {
                "doc_id": doc_id_for(record),
                "status": "ok",
                "language": lang_detector.detect_language(text or "\n".join(blocks)),
                "blocks": len(blocks),
            }
        )
    return results


def build_arg_parser() -> argparse.ArgumentParser:
    """Khai báo CLI của pipeline."""
    parser = argparse.ArgumentParser(description="Pipeline làm sạch dữ liệu DENSO A3")
    parser.add_argument(
        "--levels",
        nargs="+",
        choices=list(LEVELS),
        default=list(LEVELS),
        help="chỉ xử lý các level này (mặc định: tất cả)",
    )
    parser.add_argument("--limit", type=int, default=None, help="giới hạn số file xử lý")
    parser.add_argument(
        "--write-manifest",
        action="store_true",
        help=f"ghi {CLEANED_DIR.name}/{MANIFEST_FILENAME}",
    )
    parser.add_argument(
        "--process",
        action="store_true",
        help="chạy thử stage parse -> clean -> detect lang",
    )
    return parser


def run(argv: Sequence[str] | None = None) -> int:
    """Chạy pipeline theo CLI args; trả về exit code (0 = chạy xong không lỗi)."""
    args = build_arg_parser().parse_args(argv)

    records = discover_raw_files(tuple(args.levels))
    if args.limit is not None:
        records = records[: args.limit]

    print(f"[info] project      : {PROJECT_ROOT}")
    print(f"[info] raw dir      : {RAW_DIR.relative_to(PROJECT_ROOT).as_posix()}")
    print(f"[info] cleaned dir  : {CLEANED_DIR.relative_to(PROJECT_ROOT).as_posix()}")
    for record in records:
        print(f"  - [{record['level']}/{record['doc_type']}] {record['rel_path']}")

    if not records:
        print("[warn] chưa có file nào trong data/raw/<level_*>/", file=sys.stderr)

    if args.write_manifest:
        manifest_path = write_manifest(build_manifest(records))
        print(f"[ok] manifest -> {manifest_path.relative_to(PROJECT_ROOT).as_posix()}")

    if args.process:
        print(f"[info] chạy stage parse/clean/detect cho {len(records)} file...")
        for result in process_records(records):
            detail = result.get("reason", "")
            print(f"  - {result['status']:<11} {result['doc_id']}: {detail}".rstrip(": "))

    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Wrapper để có thể gọi từ ``python -m pipeline`` hoặc import trong test."""
    return run(argv)


if __name__ == "__main__":
    raise SystemExit(main())
