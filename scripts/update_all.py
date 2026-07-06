"""Fetch TWSE institutional trading data and update website JSON files.

This script uses only Python's standard library. It looks backward from today
until it finds the most recent TWSE T86 trading day with data, then writes:

- data/institution_trades.json
- data/investment_trust_trades.json
- data/last_updated.json
"""

from __future__ import annotations

import json
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
TWSE_T86_ENDPOINT = "https://www.twse.com.tw/rwd/zh/fund/T86"
SOURCE_NAME = "TWSE 三大法人買賣超日報 T86"
LOOKBACK_DAYS = 14
REQUEST_TIMEOUT_SECONDS = 20
REQUEST_DELAY_SECONDS = 0.35

FIELD_MAP = {
    "code": "證券代號",
    "name": "證券名稱",
    "foreign_buy": "外陸資買進股數(不含外資自營商)",
    "foreign_sell": "外陸資賣出股數(不含外資自營商)",
    "foreign_net": "外陸資買賣超股數(不含外資自營商)",
    "investment_trust_buy": "投信買進股數",
    "investment_trust_sell": "投信賣出股數",
    "investment_trust_net": "投信買賣超股數",
    "dealer_net": "自營商買賣超股數",
    "total_net": "三大法人買賣超股數",
}


def today_taipei() -> date:
    return datetime.now(timezone(timedelta(hours=8))).date()


def now_taipei_iso() -> str:
    return datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")


def to_twse_date(value: date) -> str:
    return value.strftime("%Y%m%d")


def to_iso_date(value: date | str) -> str:
    if isinstance(value, date):
        return value.isoformat()
    return f"{value[:4]}-{value[4:6]}-{value[6:8]}"


def parse_int(value: Any) -> int:
    if value in (None, "", "--"):
        return 0
    text = str(value).replace(",", "").strip()
    if text in ("", "--"):
        return 0
    return int(float(text))


def shares_to_lots(value: int) -> float:
    return round(value / 1000, 2)


def write_json(path: Path, payload: Any) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as json_file:
        json.dump(payload, json_file, ensure_ascii=False, indent=2)
        json_file.write("\n")


def build_t86_url(trade_date: date) -> str:
    query = urlencode(
        {
            "date": to_twse_date(trade_date),
            "selectType": "ALLBUT0999",
            "response": "json",
        }
    )
    return f"{TWSE_T86_ENDPOINT}?{query}"


def fetch_t86(trade_date: date) -> dict[str, Any] | None:
    url = build_t86_url(trade_date)
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 etf-tracker-data-updater/1.0",
            "Accept": "application/json,text/plain,*/*",
        },
    )

    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
        print(f"Skip {trade_date.isoformat()}: {error}")
        return None


def is_valid_payload(payload: dict[str, Any] | None) -> bool:
    if not payload:
        return False
    rows = payload.get("data") or []
    fields = payload.get("fields") or []
    return payload.get("stat") == "OK" and bool(rows) and bool(fields)


def find_latest_trading_payload(start_date: date) -> tuple[date, dict[str, Any]]:
    for offset in range(LOOKBACK_DAYS + 1):
        candidate = start_date - timedelta(days=offset)
        payload = fetch_t86(candidate)

        if is_valid_payload(payload):
            return candidate, payload

        time.sleep(REQUEST_DELAY_SECONDS)

    raise RuntimeError(f"No valid TWSE T86 data found within {LOOKBACK_DAYS} days from {start_date.isoformat()}.")


def row_to_record(fields: list[str], row: list[Any]) -> dict[str, Any] | None:
    item = dict(zip(fields, row))
    code = str(item.get(FIELD_MAP["code"], "")).strip()
    name = str(item.get(FIELD_MAP["name"], "")).strip()

    if not code or not name:
        return None

    foreign_buy = parse_int(item.get(FIELD_MAP["foreign_buy"]))
    foreign_sell = parse_int(item.get(FIELD_MAP["foreign_sell"]))
    foreign_net = parse_int(item.get(FIELD_MAP["foreign_net"]))
    investment_trust_buy = parse_int(item.get(FIELD_MAP["investment_trust_buy"]))
    investment_trust_sell = parse_int(item.get(FIELD_MAP["investment_trust_sell"]))
    investment_trust_net = parse_int(item.get(FIELD_MAP["investment_trust_net"]))
    dealer_net = parse_int(item.get(FIELD_MAP["dealer_net"]))
    total_net = parse_int(item.get(FIELD_MAP["total_net"]))

    return {
        "code": code,
        "name": name,
        "foreign_buy_shares": foreign_buy,
        "foreign_sell_shares": foreign_sell,
        "foreign_net_shares": foreign_net,
        "investment_trust_buy_shares": investment_trust_buy,
        "investment_trust_sell_shares": investment_trust_sell,
        "investment_trust_net_shares": investment_trust_net,
        "dealer_net_shares": dealer_net,
        "total_net_shares": total_net,
        "foreign_net_lots": shares_to_lots(foreign_net),
        "investment_trust_net_lots": shares_to_lots(investment_trust_net),
        "dealer_net_lots": shares_to_lots(dealer_net),
        "total_net_lots": shares_to_lots(total_net),
    }


def normalize_records(payload: dict[str, Any]) -> list[dict[str, Any]]:
    fields = payload.get("fields") or []
    rows = payload.get("data") or []
    records = []

    for row in rows:
        try:
            record = row_to_record(fields, row)
        except (TypeError, ValueError) as error:
            print(f"Skip malformed row: {error}")
            continue

        if record:
            records.append(record)

    return records


def build_institution_payload(records: list[dict[str, Any]], trade_date: date) -> dict[str, Any]:
    foreign_net = sum(item["foreign_net_shares"] for item in records)
    investment_trust_net = sum(item["investment_trust_net_shares"] for item in records)
    dealer_net = sum(item["dealer_net_shares"] for item in records)
    total_net = sum(item["total_net_shares"] for item in records)

    investment_trust_rows = [
        {
            "code": item["code"],
            "name": item["name"],
            "buySell": shares_to_lots(item["investment_trust_net_shares"]),
            "amount": 0,
        }
        for item in records
        if item["investment_trust_net_shares"] != 0
    ]
    investment_trust_rows.sort(key=lambda item: item["buySell"], reverse=True)

    return {
        "updatedAt": to_iso_date(trade_date),
        "ranges": ["day"],
        "investmentTrust": {"day": investment_trust_rows},
        "threeInstitutions": [
            {
                "date": to_iso_date(trade_date),
                "foreign": shares_to_lots(foreign_net),
                "investmentTrust": shares_to_lots(investment_trust_net),
                "dealer": shares_to_lots(dealer_net),
                "total": shares_to_lots(total_net),
            }
        ],
        "activeEtfFlows": [],
        "source": SOURCE_NAME,
        "unit": "lots",
    }


def build_investment_trust_payload(records: list[dict[str, Any]], trade_date: date) -> dict[str, Any]:
    rows = [item for item in records if item["investment_trust_net_shares"] != 0]
    buy = sorted([item for item in rows if item["investment_trust_net_shares"] > 0], key=lambda item: item["investment_trust_net_shares"], reverse=True)
    sell = sorted([item for item in rows if item["investment_trust_net_shares"] < 0], key=lambda item: item["investment_trust_net_shares"])

    def to_rank_item(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "code": item["code"],
            "name": item["name"],
            "buy_sell_shares": item["investment_trust_net_shares"],
            "buy_sell_lots": item["investment_trust_net_lots"],
            "buy_shares": item["investment_trust_buy_shares"],
            "sell_shares": item["investment_trust_sell_shares"],
        }

    return {
        "updated_at": now_taipei_iso(),
        "source": SOURCE_NAME,
        "trade_date": to_iso_date(trade_date),
        "unit": "shares",
        "buy": [to_rank_item(item) for item in buy],
        "sell": [to_rank_item(item) for item in sell],
        "all": [to_rank_item(item) for item in sorted(rows, key=lambda item: item["investment_trust_net_shares"], reverse=True)],
    }


def build_last_updated(trade_date: date, status: str, error: str | None = None) -> dict[str, Any]:
    payload = {
        "updated_at": now_taipei_iso(),
        "source": SOURCE_NAME,
        "trade_date": to_iso_date(trade_date),
        "status": status,
    }

    if error:
        payload["error"] = error

    return payload


def update_all() -> None:
    start_date = today_taipei()
    trade_date, payload = find_latest_trading_payload(start_date)
    records = normalize_records(payload)

    if not records:
        raise RuntimeError(f"TWSE T86 data for {trade_date.isoformat()} did not contain usable rows.")

    write_json(DATA_DIR / "institution_trades.json", build_institution_payload(records, trade_date))
    write_json(DATA_DIR / "investment_trust_trades.json", build_investment_trust_payload(records, trade_date))
    write_json(DATA_DIR / "last_updated.json", build_last_updated(trade_date, "success"))

    print(f"Updated TWSE data for {trade_date.isoformat()}.")
    print("Updated data/institution_trades.json")
    print("Updated data/investment_trust_trades.json")
    print("Updated data/last_updated.json")


def main() -> int:
    try:
        update_all()
        return 0
    except Exception as error:  # noqa: BLE001 - command-line scripts should report any failure clearly.
        fallback_date = today_taipei()
        write_json(DATA_DIR / "last_updated.json", build_last_updated(fallback_date, "failed", str(error)))
        print(f"Data update failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
