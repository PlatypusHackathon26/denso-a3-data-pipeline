import json
import os
from parser import parse

# Thiết lập đường dẫn thư mục hiện tại
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(CURRENT_DIR, "input_test")
OUTPUT_DIR = os.path.join(CURRENT_DIR, "output_test")


def run_test():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Quét tất cả file .docx trong input_test
    test_files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".docx")]

    if not test_files:
        print(f"⚠️ Chưa có file .docx nào trong: {INPUT_DIR}")
        print("-> Hãy copy 1 file mẫu ngắn vào thư mục này rồi chạy lại.")
        return

    for file_name in test_files:
        file_path = os.path.join(INPUT_DIR, file_name)
        print(f"🔄 Đang bóc tách: {file_name}...")

        try:
            data = parse(file_path)

            # Ghi kết quả ra output_test
            output_name = f"{os.path.splitext(file_name)[0]}.json"
            output_path = os.path.join(OUTPUT_DIR, output_name)

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f" Đã xuất kết quả kiểm tra tại: {output_path}")

        except Exception as e:
            print(f"❌ Lỗi khi xử lý {file_name}: {str(e)}")


if __name__ == "__main__":
    run_test()