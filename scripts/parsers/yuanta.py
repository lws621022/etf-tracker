"""Parse Yuanta ETF holdings from official ETF ratio pages."""

from __future__ import annotations

import json
import re
import ssl
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

REQUEST_TIMEOUT_SECONDS = 20
YUANTA_RATIO_URL = "https://www.yuantaetfs.com/product/detail/{etf_code}/ratio"


def today_taipei_iso() -> str:
    return datetime.now(timezone(timedelta(hours=8))).date().isoformat()


def normalize_date(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return today_taipei_iso()
    match = re.search(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})", text)
    if not match:
        return text
    year, month, day = match.groups()
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def parse_number(value: Any, default: float = 0) -> float:
    if value in (None, "", "--", "-"):
        return default

    text = str(value).strip().replace(",", "").replace("%", "").replace("％", "")
    if text in ("", "--", "-"):
        return default

    return float(text)


def parse_optional_shares(value: Any) -> int | None:
    if value in (None, "", "--", "-"):
        return None
    return int(round(parse_number(value)))


def decode_content(content: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp950", "big5"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="replace")


def is_ssl_verification_error(error: URLError) -> bool:
    reason = getattr(error, "reason", None)
    message = f"{reason} {error}".lower()
    return isinstance(reason, ssl.SSLError) or "certificate_verify_failed" in message or "certificate verify failed" in message


def open_yuanta_source(url: str) -> bytes:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 etf-tracker-holdings-updater/1.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        },
    )

    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            return response.read()
    except URLError as error:
        if not is_ssl_verification_error(error):
            raise

        context = ssl._create_unverified_context()
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS, context=context) as response:
            return response.read()


def find_matching_js(text: str, start: int, open_char: str, close_char: str) -> int:
    depth = 0
    quote = ""
    escape = False

    for index in range(start, len(text)):
        char = text[index]
        if quote:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == quote:
                quote = ""
            continue

        if char in ('"', "'"):
            quote = char
            continue
        if char == open_char:
            depth += 1
        elif char == close_char:
            depth -= 1
            if depth == 0:
                return index

    raise ValueError(f"找不到對應的 {close_char}")


def split_top_level_js(text: str) -> list[str]:
    parts: list[str] = []
    start = 0
    depth = 0
    quote = ""
    escape = False

    for index, char in enumerate(text):
        if quote:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == quote:
                quote = ""
            continue

        if char in ('"', "'"):
            quote = char
            continue
        if char in "[{(":
            depth += 1
        elif char in "]})":
            depth -= 1
        elif char == "," and depth == 0:
            parts.append(text[start:index].strip())
            start = index + 1

    tail = text[start:].strip()
    if tail:
        parts.append(tail)
    return parts


def parse_js_literal(token: str) -> Any:
    value = token.strip()
    if value in ("!0", "true"):
        return True
    if value in ("!1", "false"):
        return False
    if value in ("null", "void 0", "undefined"):
        return None
    if value.startswith('"'):
        return json.loads(value)
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1].replace("\\'", "'").replace('\\\\', '\\')

    try:
        return int(value)
    except ValueError:
        pass

    try:
        return float(value)
    except ValueError:
        return value


def extract_nuxt_arg_mapping(html: str) -> dict[str, Any]:
    marker = "window.__NUXT__=(function("
    marker_index = html.find(marker)
    if marker_index < 0:
        raise ValueError("找不到 Nuxt 資料區")

    params_start = marker_index + len(marker)
    params_end = html.find("){", params_start)
    if params_end < 0:
        raise ValueError("找不到 Nuxt 參數列表")

    params = [part.strip() for part in html[params_start:params_end].split(",")]
    body_start = params_end + 1
    body_end = find_matching_js(html, body_start, "{", "}")
    args_start = body_end + 1
    args_end = find_matching_js(html, args_start, "(", ")")
    args = split_top_level_js(html[args_start + 1 : args_end])

    return {param: parse_js_literal(arg) for param, arg in zip(params, args)}


def parse_js_object_fields(object_text: str, arg_mapping: dict[str, Any]) -> dict[str, Any]:
    cleaned = object_text.strip()
    if cleaned.startswith("{") and cleaned.endswith("}"):
        cleaned = cleaned[1:-1]

    payload: dict[str, Any] = {}
    for field in split_top_level_js(cleaned):
        if ":" not in field:
            continue
        key, raw_value = field.split(":", 1)
        raw_value = raw_value.strip()
        payload[key.strip()] = arg_mapping.get(raw_value, parse_js_literal(raw_value))
    return payload


def extract_stock_weights(html: str) -> list[dict[str, Any]]:
    fund_weights_index = html.find("FundWeights:{Summary")
    if fund_weights_index < 0:
        raise ValueError("找不到元大 FundWeights 資料")

    stock_weights_index = html.find("StockWeights:[", fund_weights_index)
    if stock_weights_index < 0:
        raise ValueError("找不到元大 StockWeights 資料")

    array_start = html.find("[", stock_weights_index)
    array_end = find_matching_js(html, array_start, "[", "]")
    object_texts = split_top_level_js(html[array_start + 1 : array_end])
    arg_mapping = extract_nuxt_arg_mapping(html)

    return [parse_js_object_fields(item, arg_mapping) for item in object_texts if item.strip()]


def extract_trade_date(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    match = re.search(r"(?:交易日期|Trade Date)\s*:?\s*(\d{4}[/-]\d{1,2}[/-]\d{1,2})", text)
    return normalize_date(match.group(1)) if match else today_taipei_iso()


def parse_yuanta_holdings_page(html: str, etf_code: str, etf_name: str, source_url: str) -> list[dict[str, Any]]:
    data_date = extract_trade_date(html)
    rows: list[dict[str, Any]] = []

    for item in extract_stock_weights(html):
        stock_code = str(item.get("code") or "").strip()
        stock_name = str(item.get("name") or "").strip()
        if not stock_code or not stock_name:
            continue

        rows.append(
            {
                "etf_code": etf_code,
                "etf_name": etf_name,
                "stock_code": stock_code,
                "stock_name": stock_name,
                "weight": round(parse_number(item.get("weights")), 4),
                "shares": parse_optional_shares(item.get("qty")),
                "data_date": data_date,
                "source": "auto",
                "source_url": source_url,
            }
        )

    if len(rows) < 10:
        raise ValueError(f"元大持股資料不足 10 筆：只解析到 {len(rows)} 筆")
    return rows


def fetch_yuanta_holdings(etf_code: str, etf_name: str, source_url: str | None = None) -> tuple[list[dict[str, Any]], str]:
    url = source_url or YUANTA_RATIO_URL.format(etf_code=etf_code)
    html = decode_content(open_yuanta_source(url))
    return parse_yuanta_holdings_page(html, etf_code, etf_name, url), url
