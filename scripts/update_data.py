"""Convert CSV source files into website JSON data.

The script intentionally uses only Python's standard library so it can run on a
plain Windows Python installation. Put CSV files in sources/ and run:

    python scripts/update_data.py
"""

from __future__ import annotations

import csv
import json
from collections import OrderedDict
from pathlib import Path
from typing import Iterable

ROOT_DIR = Path(__file__).resolve().parents[1]
SOURCES_DIR = ROOT_DIR / "sources"
DATA_DIR = ROOT_DIR / "data"

RANGE_ORDER = ["day", "5d", "20d", "60d"]


def read_csv(filename: str) -> list[dict[str, str]]:
    path = SOURCES_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing source CSV: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        return [normalize_row(row) for row in csv.DictReader(csv_file)]


def normalize_row(row: dict[str, str | None]) -> dict[str, str]:
    return {key.strip(): (value or "").strip() for key, value in row.items() if key}


def write_json(filename: str, payload: object) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    path = DATA_DIR / filename
    with path.open("w", encoding="utf-8", newline="\n") as json_file:
        json.dump(payload, json_file, ensure_ascii=False, indent=2)
        json_file.write("\n")


def require(row: dict[str, str], fields: Iterable[str], source: str) -> None:
    missing = [field for field in fields if not row.get(field)]
    if missing:
        raise ValueError(f"{source} row is missing required field(s): {', '.join(missing)}")


def get_value(row: dict[str, str], *fields: str) -> str:
    for field in fields:
        if row.get(field):
            return row[field]
    return ""


def to_float(value: str, default: float = 0.0) -> float:
    if value == "":
        return default
    return float(value.replace(",", ""))


def to_int(value: str, default: int = 0) -> int:
    if value == "":
        return default
    return int(float(value.replace(",", "")))


def to_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y", "是"}


def build_etf_list() -> list[dict[str, object]]:
    rows = read_csv("etf_list.csv")
    etfs: list[dict[str, object]] = []

    for row in rows:
        require(row, ["code", "name"], "etf_list.csv")
        etfs.append(
            {
                "code": row["code"],
                "name": row["name"],
                "type": row.get("type", ""),
                "issuer": row.get("issuer", ""),
                "category": row.get("category", ""),
                "aum": to_float(row.get("aum", "")),
                "expenseRatio": to_float(row.get("expenseRatio", "")),
                "price": to_float(row.get("price", "")),
                "changePct": to_float(row.get("changePct", "")),
                "yield": to_float(row.get("yield", "")),
                "trackingIndex": row.get("trackingIndex", ""),
                "isActive": to_bool(row.get("isActive", "")),
            }
        )

    return etfs


def build_etf_holdings() -> list[dict[str, object]]:
    rows = read_csv("etf_holdings.csv")
    holdings: list[dict[str, object]] = []

    for row in rows:
        required_groups = {
            "etf_code": get_value(row, "etf_code", "etfCode"),
            "etf_name": get_value(row, "etf_name", "etfName"),
            "stock_code": get_value(row, "stock_code", "stockCode"),
            "stock_name": get_value(row, "stock_name", "stockName"),
        }
        missing = [field for field, value in required_groups.items() if not value]
        if missing:
            raise ValueError(f"etf_holdings.csv row is missing required field(s): {', '.join(missing)}")

        holdings.append(
            {
                "etf_code": required_groups["etf_code"],
                "etf_name": required_groups["etf_name"],
                "stock_code": required_groups["stock_code"],
                "stock_name": required_groups["stock_name"],
                "weight": to_float(row.get("weight", "")),
                "shares": to_int(row.get("shares", "")),
            }
        )

    return holdings


def build_institution_trades() -> dict[str, object]:
    rows = read_csv("institution_trades.csv")
    investment_trust: dict[str, list[dict[str, object]]] = OrderedDict((key, []) for key in RANGE_ORDER)
    three_institutions: list[dict[str, object]] = []
    active_etf_flows: list[dict[str, object]] = []
    updated_at = ""

    for row in rows:
        record_type = row.get("recordType", "")
        updated_at = row.get("updatedAt") or updated_at

        if record_type == "investment_trust":
            require(row, ["range", "code", "name"], "institution_trades.csv")
            investment_trust.setdefault(row["range"], []).append(
                {
                    "code": row["code"],
                    "name": row["name"],
                    "buySell": to_int(row.get("buySell", "")),
                    "amount": to_float(row.get("amount", "")),
                }
            )
        elif record_type == "three_institutions":
            require(row, ["date"], "institution_trades.csv")
            three_institutions.append(
                {
                    "date": row["date"],
                    "foreign": to_float(row.get("foreign", "")),
                    "investmentTrust": to_float(row.get("investmentTrust", "")),
                    "dealer": to_float(row.get("dealer", "")),
                    "total": to_float(row.get("total", "")),
                }
            )
        elif record_type == "active_etf_flow":
            require(row, ["etfCode", "etfName", "stockCode", "stockName", "action"], "institution_trades.csv")
            active_etf_flows.append(
                {
                    "etfCode": row["etfCode"],
                    "etfName": row["etfName"],
                    "stockCode": row["stockCode"],
                    "stockName": row["stockName"],
                    "action": row["action"],
                    "weightChange": to_float(row.get("weightChange", "")),
                    "sharesChange": to_int(row.get("sharesChange", "")),
                }
            )
        else:
            raise ValueError(f"Unknown recordType in institution_trades.csv: {record_type}")

    ranges = [key for key, value in investment_trust.items() if value]
    return {
        "updatedAt": updated_at,
        "ranges": ranges,
        "investmentTrust": {key: investment_trust[key] for key in ranges},
        "threeInstitutions": three_institutions,
        "activeEtfFlows": active_etf_flows,
    }


def build_price_history() -> dict[str, object]:
    rows = read_csv("price_history.csv")
    dates: list[str] = []
    series: dict[str, list[float]] = OrderedDict()
    nav_series: dict[str, list[float]] = OrderedDict()

    for row in rows:
        require(row, ["date", "etfCode", "price"], "price_history.csv")
        date = row["date"]
        etf_code = row["etfCode"]

        if date not in dates:
            dates.append(date)

        series.setdefault(etf_code, []).append(to_float(row["price"]))
        if row.get("nav"):
            nav_series.setdefault(etf_code, []).append(to_float(row["nav"]))

    payload: dict[str, object] = {"dates": dates, "series": series}
    if nav_series:
        payload["navSeries"] = nav_series
    return payload


def main() -> None:
    outputs = {
        "etf_list.json": build_etf_list(),
        "etf_holdings.json": build_etf_holdings(),
        "institution_trades.json": build_institution_trades(),
        "price_history.json": build_price_history(),
    }

    for filename, payload in outputs.items():
        write_json(filename, payload)
        print(f"Updated data/{filename}")

    print("Data update complete.")


if __name__ == "__main__":
    main()
