"""Convert downloaded ETF holding CSV files into data/etf_holdings.json.

Put source files in sources/holdings/ with names like:

- 0050_yuanta.csv
- 00878_cathay.csv
- 00919_capital.csv

The converter accepts common Chinese and English column names from different
asset managers and reports the filename when required columns cannot be mapped.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path
from typing import Iterable

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
HOLDINGS_DIR = ROOT_DIR / "sources" / "holdings"
OUTPUT_PATH = DATA_DIR / "etf_holdings.json"
ETF_LIST_PATH = DATA_DIR / "etf_list.json"

COLUMN_ALIASES = {
    "etf_code": ["etf_code", "etf code", "etf代號", "基金代號", "股票型基金代號"],
    "etf_name": ["etf_name", "etf name", "etf名稱", "基金名稱", "股票型基金名稱"],
    "stock_code": ["stock_code", "stock code", "股票代號", "證券代號", "持股代號", "成分股代號", "標的代號", "代號"],
    "stock_name": ["stock_name", "stock name", "股票名稱", "證券名稱", "持股名稱", "成分股名稱", "標的名稱", "名稱"],
    "weight": ["weight", "weight_pct", "weight %", "持股比例", "持股比率", "權重", "比重", "比例", "占基金淨資產比例", "占淨資產比例", "%"],
    "shares": ["shares", "share", "units", "持有股數", "持有張數", "股數", "張數", "數量", "持股數", "持有數量"],
}

REQUIRED_FIELDS = ["stock_code", "stock_name", "weight", "shares"]
SUPPORTED_SUFFIXES = {".csv"}


def normalize_header(value: str) -> str:
    text = value.strip().lower()
    text = text.replace("（", "(").replace("）", ")")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[\ufeff：:()（）％%]", "", text)
    return text.replace("_", " ").strip()


def normalize_key(value: str) -> str:
    return normalize_header(value).replace(" ", "")


def build_alias_lookup() -> dict[str, str]:
    lookup: dict[str, str] = {}
    for field, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            lookup[normalize_key(alias)] = field
    return lookup


def parse_number(value: str, default: float = 0.0) -> float:
    text = str(value or "").strip()
    if not text or text in {"-", "--", "—"}:
        return default
    text = text.replace(",", "").replace("%", "").replace("％", "")
    return float(text)


def parse_int(value: str, default: int = 0) -> int:
    return int(round(parse_number(value, float(default))))


def read_etf_names() -> dict[str, str]:
    if not ETF_LIST_PATH.exists():
        return {}

    with ETF_LIST_PATH.open("r", encoding="utf-8") as json_file:
        rows = json.load(json_file)

    return {str(row.get("code", "")).strip(): str(row.get("name", "")).strip() for row in rows if row.get("code")}


def get_etf_code_from_filename(path: Path) -> str:
    match = re.match(r"^([0-9A-Za-z]+)", path.stem)
    return match.group(1).upper() if match else ""


def detect_columns(headers: Iterable[str]) -> dict[str, str]:
    alias_lookup = build_alias_lookup()
    detected: dict[str, str] = {}

    for header in headers:
        normalized = normalize_key(header)
        field = alias_lookup.get(normalized)
        if field and field not in detected:
            detected[field] = header

    return detected


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        sample = csv_file.read(4096)
        csv_file.seek(0)
        dialect = csv.Sniffer().sniff(sample) if sample.strip() else csv.excel
        reader = csv.DictReader(csv_file, dialect=dialect)
        return [{key: (value or "").strip() for key, value in row.items() if key} for row in reader]


def validate_columns(path: Path, detected: dict[str, str]) -> None:
    missing = [field for field in REQUIRED_FIELDS if field not in detected]
    if missing:
        readable = ", ".join(missing)
        raise ValueError(f"{path}: 無法辨識必要欄位：{readable}。請檢查欄位名稱或補上對應欄位。")


def convert_file(path: Path, etf_names: dict[str, str]) -> list[dict[str, object]]:
    if path.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise ValueError(f"{path}: 目前僅支援 CSV。若要讀取 Excel，請先另存為 CSV 後再執行。")

    rows = read_csv_rows(path)
    if not rows:
        return []

    detected = detect_columns(rows[0].keys())
    validate_columns(path, detected)

    filename_etf_code = get_etf_code_from_filename(path)
    converted: list[dict[str, object]] = []

    for row_index, row in enumerate(rows, start=2):
        stock_code = row.get(detected["stock_code"], "").strip()
        stock_name = row.get(detected["stock_name"], "").strip()

        if not stock_code and not stock_name:
            continue

        if not stock_code or not stock_name:
            raise ValueError(f"{path}: 第 {row_index} 列缺少股票代號或股票名稱。")

        etf_code = row.get(detected.get("etf_code", ""), "").strip().upper() if "etf_code" in detected else filename_etf_code
        if not etf_code:
            raise ValueError(f"{path}: 無法從檔名或欄位辨識 ETF 代號。檔名請使用 0050_yuanta.csv 這類格式。")

        etf_name = row.get(detected.get("etf_name", ""), "").strip() if "etf_name" in detected else etf_names.get(etf_code, "")
        if not etf_name:
            etf_name = etf_code

        converted.append(
            {
                "etf_code": etf_code,
                "etf_name": etf_name,
                "stock_code": stock_code,
                "stock_name": stock_name,
                "weight": parse_number(row.get(detected["weight"], "")),
                "shares": parse_int(row.get(detected["shares"], "")),
            }
        )

    return converted


def find_source_files() -> list[Path]:
    if not HOLDINGS_DIR.exists():
        raise FileNotFoundError(f"找不到資料夾：{HOLDINGS_DIR}。請建立 sources/holdings/ 並放入持股 CSV。")

    return sorted(path for path in HOLDINGS_DIR.iterdir() if path.is_file() and not path.name.startswith("."))


def write_output(rows: list[dict[str, object]]) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8", newline="\n") as json_file:
        json.dump(rows, json_file, ensure_ascii=False, indent=2)
        json_file.write("\n")


def main() -> int:
    try:
        etf_names = read_etf_names()
        source_files = find_source_files()
        all_holdings: list[dict[str, object]] = []

        for source_file in source_files:
            rows = convert_file(source_file, etf_names)
            all_holdings.extend(rows)
            print(f"Converted {source_file}: {len(rows)} rows")

        all_holdings.sort(key=lambda item: (str(item["etf_code"]), -float(item["weight"]), str(item["stock_code"])))
        write_output(all_holdings)
        print(f"Updated {OUTPUT_PATH}: {len(all_holdings)} rows")
        return 0
    except Exception as error:  # noqa: BLE001 - command-line scripts should print actionable file errors.
        print(f"ETF holdings conversion failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
