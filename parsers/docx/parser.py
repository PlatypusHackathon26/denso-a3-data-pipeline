import hashlib
import os
from datetime import datetime, timezone
from docx import Document


def table_to_markdown(table) -> str:
    """Chuyển đổi table của docx sang Markdown Table chuẩn."""
    md_rows = []
    for i, row in enumerate(table.rows):
        row_cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
        md_row = "| " + " | ".join(row_cells) + " |"
        md_rows.append(md_row)
        if i == 0:
            separator = "| " + " | ".join(["---"] * len(row.cells)) + " |"
            md_rows.append(separator)
    return "\n".join(md_rows)


def parse(file_path: str, access_level: int = 1) -> dict:
    """Bóc tách file .docx theo schema chuẩn Denso A3."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Không tìm thấy file: {file_path}")

    filename = os.path.basename(file_path)
    file_size_kb = round(os.path.getsize(file_path) / 1024, 1)

    # Sinh doc_id duy nhất dựa trên tên file và hash ngắn
    name_hash = hashlib.md5(filename.encode()).hexdigest()[:8].upper()
    doc_id = f"DENSO_{name_hash}"

    doc = Document(file_path)

    # 1. Trích xuất text và nhận diện chuyển trang qua ký tự 'page' hoặc ngắt trang
    pages_text = []
    current_page = []

    for p in doc.paragraphs:
        text = p.text.strip()
        if not text:
            continue

        # Kiểm tra nếu đoạn chứa ngắt trang (Page Break)
        has_page_break = any(
            "lastRenderedPageBreak" in run._r.xml or "w:br" in run._r.xml
            for run in p.runs
        )

        if has_page_break and current_page:
            pages_text.append("\n\n".join(current_page))
            current_page = [text]
        else:
            current_page.append(text)

    if current_page:
        pages_text.append("\n\n".join(current_page))

    # Ghép chuỗi cleaned_text có header từng trang
    cleaned_text_parts = []
    for idx, page_content in enumerate(pages_text, start=1):
        cleaned_text_parts.append(f"--- [Trang {idx}] ---\n{page_content}")
    cleaned_text = "\n\n".join(cleaned_text_parts)

    # 2. Trích xuất bảng (Gán mặc định trang ước lượng hoặc trang 1)
    tables_data = []
    for idx, table in enumerate(doc.tables, start=1):
        md_content = table_to_markdown(table)
        tables_data.append({
            "page": min(idx, len(pages_text)) if pages_text else 1,
            "markdown": md_content,
        })

    # 3. Đóng gói kết quả theo đúng cấu trúc yêu cầu
    return {
        "doc_id": doc_id,
        "source_file": filename,
        "source_type": "docx",
        "language": "vi",
        "access_level": access_level,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "cleaned_text": cleaned_text,
        "tables": tables_data,
        "metadata": {
            "total_pages": max(len(pages_text), 1),
            "file_size_kb": file_size_kb,
            "is_corrupted": False,
        },
    }