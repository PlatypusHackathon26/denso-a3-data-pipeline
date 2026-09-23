# DENSO A3 Data Pipeline

Pipeline boc tach tai lieu theo tung loai file va xu ly du lieu theo ba cap
`level_1`, `level_2`, `level_3`.

## Cau truc

- `parsers/<type>/`: parser doc lap, input mau, output test va test cuc bo.
- `pipeline/`: module dieu phoi trung tam va du lieu test tich hop.
- `data/raw/`: du lieu goc san xuat, chi luu local.
- `data/cleaned_json/`: JSON thanh pham cho Vector DB, khong commit output tu sinh.
- `utils/`: cac ham dung chung.

## Chay pipeline hien tai

```powershell
python pipeline.py
python pipeline.py --write-manifest
python pipeline.py --process
```

Them file vao `data/raw/level_1/`, `data/raw/level_2/` hoac
`data/raw/level_3/` de pipeline phat hien. Schema dau ra duoc mo ta trong
`output_format.json`.

## Cai dat

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Mot so parser can them binary ngoai (vi du Tesseract hoac FFmpeg); xem ghi
chu trong `requirements.txt` truoc khi bat cac dependency tuong ung.