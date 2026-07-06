"""Update ETF holdings data with CSV fallback and preservation rules.

The first version keeps the auto-fetch layer intentionally pluggable. When no
auto source is configured, or when an auto fetch fails, the script looks for a
manual CSV file in sources/holdings/{etf_code}.csv. If that also fails, existing
holdings for that ETF are preserved so one broken source does not clear data.
"""

from __future__ import annotations

import csv
import io
import json
import ssl
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
SOURCES_DIR = ROOT_DIR / "sources" / "holdings"
HOLDINGS_PATH = DATA_DIR / "etf_holdings.json"
REPORT_PATH = DATA_DIR / "holdings_update_report.json"
REQUEST_TIMEOUT_SECONDS = 20

SUPPORTED_ETFS: dict[str, dict[str, str]] = {
    "0050": {"name": "元大台灣50", "auto_url": ""},
    "0056": {"name": "元大高股息", "auto_url": ""},
    "006208": {"name": "富邦台50", "auto_url": ""},
    "00878": {"name": "國泰永續高股息", "auto_url": ""},
    "00919": {"name": "群益台灣精選高息", "auto_url": ""},
}

COLUMN_ALIASES = {
    "stock_code": ["股票代號", "stock_code", "code", "證券代號", "代號"],
    "stock_name": ["股票名稱", "stock_name", "name", "證券名稱", "名稱"],
    "weight": ["持股比例", "weight", "ratio", "權重", "比重", "持股比率"],
    "shares": ["持有股數", "shares", "股數", "持股數", "持有股數(股)"],
    "lots": ["持有張數", "lots", "張數", "持股張數"],
    "data_date": ["資料日期", "data_date", "date", "日期"],
}


def now_taipei() -> datetime:
    return datetime.now(timezone(timedelta(hours=8)))


def today_taipei_iso() -> str:
    return now_taipei().date().isoformat()


def normalize_header(value: str) -> str:
    return value.strip().lower().replace(" ", "").replace("_", "")


def parse_number(value: Any, default: float = 0) -> float:
    if value in (None, "", "--", "-"):
        return default

    text = str(value).strip().replace(",", "").replace("%", "").replace("％", "")
    if text in ("", "--", "-"):
        return default

    return float(text)


def parse_shares(value: Any) -> int:
    return int(round(parse_number(value)))


def read_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback

    with path.open("r", encoding="utf-8") as json_file:
        return json.load(json_file)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as json_file:
        json.dump(payload, json_file, ensure_ascii=False, indent=2)
        json_file.write("\n")


def read_existing_holdings() -> list[dict[str, Any]]:
    payload = read_json(HOLDINGS_PATH, [])
    if not isinstance(payload, list):
        return []
    return [item for item in payload if isinstance(item, dict)]


def normalize_existing_holding(row: dict[str, Any], etf_code: str | None = None, etf_name: str | None = None) -> dict[str, Any]:
    code = etf_code or str(row.get("etf_code") or row.get("etfCode") or "").strip()
    name = etf_name or str(row.get("etf_name") or row.get("etfName") or "").strip()

    return {
        "etf_code": code,
        "etf_name": name,
        "stock_code": str(row.get("stock_code") or row.get("stockCode") or "").strip(),
        "stock_name": str(row.get("stock_name") or row.get("stockName") or "").strip(),
        "weight": parse_number(row.get("weight")),
        "shares": parse_shares(row.get("shares")),
        "data_date": str(row.get("data_date") or ""),
        "source": str(row.get("source") or "previous"),
        "source_url": str(row.get("source_url") or ""),
    }


def group_holdings_by_etf(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        etf_code = str(row.get("etf_code") or row.get("etfCode") or "").strip()
        if etf_code:
            grouped[etf_code].append(row)
    return grouped


def decode_csv_bytes(content: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp950", "big5"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="replace")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("rb") as csv_file:
        content = decode_csv_bytes(csv_file.read())
    return parse_csv_content(content, source_label=str(path))


def parse_csv_content(content: str, source_label: str) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(content))
    if not reader.fieldnames:
        raise ValueError(f"{source_label} 沒有可辨識的 CSV 標題列")
    return [dict(row) for row in reader]


def detect_columns(fieldnames: list[str], source_label: str) -> dict[str, str]:
    normalized_to_original = {normalize_header(field): field for field in fieldnames if field}
    columns: dict[str, str] = {}

    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            original = normalized_to_original.get(normalize_header(alias))
            if original:
                columns[canonical] = original
                break

    missing = ["stock_code", "stock_name", "weight"]
    missing_required = [field for field in missing if field not in columns]
    if "shares" not in columns and "lots" not in columns:
        missing_required.append("shares 或 lots")

    if missing_required:
        raise ValueError(f"{source_label} 欄位無法辨識：{', '.join(missing_required)}")

    return columns


def normalize_holding_rows(
    rows: list[dict[str, Any]],
    *,
    etf_code: str,
    etf_name: str,
    source: str,
    source_url: str,
) -> list[dict[str, Any]]:
    if not rows:
        raise ValueError("沒有持股資料列")

    fieldnames = list(rows[0].keys())
    columns = detect_columns(fieldnames, source_url or source)
    default_data_date = today_taipei_iso()
    normalized: list[dict[str, Any]] = []

    for row in rows:
        stock_code = str(row.get(columns["stock_code"], "")).strip()
        stock_name = str(row.get(columns["stock_name"], "")).strip()
        if not stock_code or not stock_name:
            continue

        if "shares" in columns:
            shares = parse_shares(row.get(columns["shares"]))
        else:
            shares = parse_shares(parse_number(row.get(columns["lots"])) * 1000)

        data_date = default_data_date
        if "data_date" in columns:
            data_date = str(row.get(columns["data_date"]) or default_data_date).strip()

        normalized.append(
            {
                "etf_code": etf_code,
                "etf_name": etf_name,
                "stock_code": stock_code,
                "stock_name": stock_name,
                "weight": round(parse_number(row.get(columns["weight"])), 4),
                "shares": shares,
                "data_date": data_date,
                "source": source,
                "source_url": source_url,
            }
        )

    if not normalized:
        raise ValueError("沒有可用的持股資料列")

    return normalized


def open_auto_source(url: str) -> bytes:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 etf-tracker-holdings-updater/1.0",
            "Accept": "text/csv,application/json,text/plain,*/*",
        },
    )

    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            return response.read()
    except URLError as error:
        reason = getattr(error, "reason", None)
        message = f"{reason} {error}".lower()
        if not isinstance(reason, ssl.SSLError) and "certificate_verify_failed" not in message:
            raise

        context = ssl._create_unverified_context()
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS, context=context) as response:
            return response.read()


def fetch_auto_holdings(etf_code: str, config: dict[str, str]) -> tuple[list[dict[str, Any]], str]:
    url = config.get("auto_url", "").strip()
    if not url:
        raise RuntimeError("尚未設定自動抓取來源")

    content = open_auto_source(url)
    text = decode_csv_bytes(content)
    rows = parse_csv_content(text, source_label=url)
    holdings = normalize_holding_rows(
        rows,
        etf_code=etf_code,
        etf_name=config["name"],
        source="auto",
        source_url=url,
    )
    return holdings, url


def load_csv_fallback(etf_code: str, etf_name: str) -> tuple[list[dict[str, Any]], str]:
    csv_path = SOURCES_DIR / f"{etf_code}.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"找不到 CSV 備援資料 {csv_path.relative_to(ROOT_DIR).as_posix()}")

    source_path = csv_path.relative_to(ROOT_DIR).as_posix()
    rows = read_csv_rows(csv_path)
    holdings = normalize_holding_rows(
        rows,
        etf_code=etf_code,
        etf_name=etf_name,
        source="csv",
        source_url=source_path,
    )
    return holdings, source_path


def preserve_existing_rows(
    existing_by_code: dict[str, list[dict[str, Any]]],
    etf_code: str,
    etf_name: str,
) -> list[dict[str, Any]]:
    return [normalize_existing_holding(row, etf_code, etf_name) for row in existing_by_code.get(etf_code, [])]


def build_report_item(
    *,
    etf_code: str,
    etf_name: str,
    status: str,
    source: str,
    data_date: str,
    message: str,
) -> dict[str, str]:
    return {
        "etf_code": etf_code,
        "etf_name": etf_name,
        "status": status,
        "source": source,
        "data_date": data_date,
        "message": message,
    }


def pick_data_date(rows: list[dict[str, Any]]) -> str:
    for row in rows:
        data_date = str(row.get("data_date") or "").strip()
        if data_date:
            return data_date
    return today_taipei_iso()


def update_holdings() -> dict[str, Any]:
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    existing_rows = read_existing_holdings()
    existing_by_code = group_holdings_by_etf(existing_rows)
    output_by_code: dict[str, list[dict[str, Any]]] = {}
    report_items: list[dict[str, str]] = []

    for etf_code, config in SUPPORTED_ETFS.items():
        etf_name = config["name"]
        auto_error = ""

        try:
            holdings, auto_source_url = fetch_auto_holdings(etf_code, config)
            output_by_code[etf_code] = holdings
            report_items.append(
                build_report_item(
                    etf_code=etf_code,
                    etf_name=etf_name,
                    status="success",
                    source="auto",
                    data_date=pick_data_date(holdings),
                    message="",
                )
            )
            print(f"Updated {etf_code} from auto source: {auto_source_url}")
            continue
        except (HTTPError, URLError, TimeoutError, OSError, RuntimeError, ValueError) as error:
            auto_error = str(error)

        try:
            holdings, csv_source = load_csv_fallback(etf_code, etf_name)
            output_by_code[etf_code] = holdings
            report_items.append(
                build_report_item(
                    etf_code=etf_code,
                    etf_name=etf_name,
                    status="fallback_csv",
                    source=csv_source,
                    data_date=pick_data_date(holdings),
                    message="自動抓取失敗，已改用 CSV 備援資料",
                )
            )
            print(f"Updated {etf_code} from CSV fallback: {csv_source}")
            continue
        except (FileNotFoundError, OSError, ValueError) as csv_error:
            preserved = preserve_existing_rows(existing_by_code, etf_code, etf_name)
            output_by_code[etf_code] = preserved
            detail = f"自動抓取失敗：{auto_error}；CSV 備援失敗：{csv_error}"
            if preserved:
                detail = f"{detail}。使用最近一次資料"
            report_items.append(
                build_report_item(
                    etf_code=etf_code,
                    etf_name=etf_name,
                    status="failed",
                    source="previous" if preserved else "",
                    data_date=pick_data_date(preserved) if preserved else "",
                    message=detail,
                )
            )
            print(f"Skipped {etf_code}: {detail}", file=sys.stderr)

    final_rows: list[dict[str, Any]] = []
    for row in existing_rows:
        etf_code = str(row.get("etf_code") or row.get("etfCode") or "").strip()
        if etf_code and etf_code not in SUPPORTED_ETFS:
            final_rows.append(normalize_existing_holding(row))

    for etf_code in SUPPORTED_ETFS:
        final_rows.extend(output_by_code.get(etf_code, []))

    final_rows.sort(key=lambda item: (item["etf_code"], -item["weight"], item["stock_code"]))
    write_json(HOLDINGS_PATH, final_rows)

    summary = {"success": 0, "fallback_csv": 0, "failed": 0, "skipped": 0}
    for item in report_items:
        summary[item["status"]] = summary.get(item["status"], 0) + 1

    report = {
        "updated_at": now_taipei().isoformat(timespec="seconds"),
        "summary": summary,
        "items": report_items,
    }
    write_json(REPORT_PATH, report)

    print("Updated data/etf_holdings.json")
    print("Updated data/holdings_update_report.json")
    return report


def main() -> int:
    try:
        update_holdings()
        return 0
    except Exception as error:  # noqa: BLE001 - command-line scripts should report any failure clearly.
        print(f"ETF holdings update failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
