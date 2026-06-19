#!/usr/bin/env python3
"""Fetch and normalize Sporttery football odds.

This script is deliberately defensive because Sporttery's public JSON shape can
change. It searches each response for match-like dictionaries, then merges them
by match number or team/date fallback.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import json
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


BASE_URL = "https://webapi.sporttery.cn/gateway/uniform/football/getMatchCalculatorV1.qry"
DEFAULT_POOL_CODES = ("hhad,had", "crs", "ttg", "hafu")
BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)
POOL_NAMES = {
    "had": "胜平负",
    "hhad": "让球胜平负",
    "crs": "比分",
    "ttg": "总进球",
    "hafu": "半全场",
}
ODDS_FIELDS = ("had", "hhad", "crs", "ttg", "hafu")
IDENTITY_FIELDS = (
    "businessDate",
    "matchNumStr",
    "homeTeamAllName",
    "awayTeamAllName",
    "leagueAllName",
    "matchDate",
    "matchTime",
    "matchStatus",
)


def parse_datetime(date_value: Any, time_value: Any) -> dt.datetime | None:
    if not date_value or not time_value:
        return None
    try:
        return dt.datetime.fromisoformat(f"{date_value} {time_value}")
    except ValueError:
        return None


def sales_stop_for_date(date_value: str) -> dt.datetime | None:
    try:
        sale_date = dt.date.fromisoformat(date_value)
    except ValueError:
        return None
    stop_hour = 23 if sale_date.weekday() >= 5 else 22
    return dt.datetime.combine(sale_date, dt.time(stop_hour, 0))


def sales_open_for_date(date_value: str) -> dt.datetime | None:
    try:
        sale_date = dt.date.fromisoformat(date_value)
    except ValueError:
        return None
    return dt.datetime.combine(sale_date, dt.time(11, 0))


def computed_times(identity: dict[str, Any]) -> dict[str, str | None]:
    sale_date = str(identity.get("businessDate") or identity.get("matchDate") or "")
    kickoff = parse_datetime(identity.get("matchDate"), identity.get("matchTime"))
    sale_open = sales_open_for_date(sale_date) if sale_date else None
    sale_stop = sales_stop_for_date(sale_date) if sale_date else None
    cutoff = None
    if kickoff and sale_stop:
        cutoff = min(kickoff, sale_stop)
    elif kickoff:
        cutoff = kickoff
    elif sale_stop:
        cutoff = sale_stop
    return {
        "sale_date": sale_date or None,
        "sale_open": sale_open.isoformat(sep=" ") if sale_open else None,
        "official_sale_stop": sale_stop.isoformat(sep=" ") if sale_stop else None,
        "kickoff": kickoff.isoformat(sep=" ") if kickoff else None,
        "computed_cutoff": cutoff.isoformat(sep=" ") if cutoff else None,
        "rule": "cutoff = min(kickoff, official_sale_stop); sale window opens 11:00, stops 22:00 Mon-Fri and 23:00 Sat-Sun by sale date",
    }


def fetch_pool(pool_code: str, timeout: float, insecure: bool = False) -> dict[str, Any]:
    query = urllib.parse.urlencode({"channel": "c"})
    query = f"{query}&poolCode={urllib.parse.quote(pool_code, safe=',')}"
    request = urllib.request.Request(
        f"{BASE_URL}?{query}",
        headers={
            "Accept": "application/json,text/plain,*/*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Origin": "https://www.sporttery.cn",
            "Referer": "https://www.sporttery.cn/",
            "User-Agent": BROWSER_USER_AGENT,
        },
    )
    context = ssl._create_unverified_context() if insecure else None
    with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
        body = response.read().decode("utf-8")
    payload = json.loads(body)
    return {"poolCode": pool_code, "payload": payload}


def iter_match_dicts(value: Any) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    if isinstance(value, dict):
        if "matchNumStr" in value and (
            "homeTeamAllName" in value or "awayTeamAllName" in value
        ):
            matches.append(value)
        for child in value.values():
            matches.extend(iter_match_dicts(child))
    elif isinstance(value, list):
        for item in value:
            matches.extend(iter_match_dicts(item))
    return matches


def match_key(match: dict[str, Any]) -> str:
    if match.get("matchNumStr"):
        return str(match["matchNumStr"])
    parts = [
        str(match.get("matchDate", "")),
        str(match.get("matchTime", "")),
        str(match.get("homeTeamAllName", "")),
        str(match.get("awayTeamAllName", "")),
    ]
    return "|".join(parts)


def parse_single_status(match: dict[str, Any]) -> dict[str, dict[str, Any]]:
    status: dict[str, dict[str, Any]] = {}
    pool_list = match.get("poolList") or []
    if not isinstance(pool_list, list):
        return status
    for item in pool_list:
        if not isinstance(item, dict):
            continue
        code = str(item.get("poolCode") or item.get("poolcode") or "").lower()
        if not code:
            continue
        single = item.get("single")
        status[code] = {
            "name": POOL_NAMES.get(code, code),
            "single": single,
            "single_label": "单关" if str(single) == "1" else "仅过关",
            "poolStatus": item.get("poolStatus"),
        }
    return status


def compact_odds(match: dict[str, Any]) -> dict[str, Any]:
    odds: dict[str, Any] = {}
    for field in ODDS_FIELDS:
        value = match.get(field)
        if isinstance(value, dict) and value:
            odds[field] = value
    return odds


def merge_matches(pool_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for result in pool_results:
        pool_code = result["poolCode"]
        for match in iter_match_dicts(result["payload"]):
            key = match_key(match)
            record = merged.setdefault(
                key,
                {
                    "key": key,
                    "sources": [],
                    "identity": {},
                    "odds": {},
                    "pool_status": {},
                    "raw_match_refs": 0,
                },
            )
            record["sources"].append(pool_code)
            record["raw_match_refs"] += 1
            for field in IDENTITY_FIELDS:
                if match.get(field) is not None:
                    record["identity"][field] = match.get(field)
            record["odds"].update(compact_odds(match))
            record["pool_status"].update(parse_single_status(match))
            record["computed_times"] = computed_times(record["identity"])
    return sorted(
        merged.values(),
        key=lambda item: (
            str(item["identity"].get("matchDate", "")),
            str(item["identity"].get("matchTime", "")),
            str(item["identity"].get("matchNumStr", "")),
        ),
    )


def cli() -> int:
    parser = argparse.ArgumentParser(description="Fetch Sporttery football odds as normalized JSON.")
    parser.add_argument(
        "--pool-code",
        action="append",
        dest="pool_codes",
        help="Pool code to fetch. Repeatable. Defaults to hhad,had / crs / ttg / hafu.",
    )
    parser.add_argument("--timeout", type=float, default=12.0, help="HTTP timeout in seconds.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable TLS certificate verification for trusted local proxy environments.",
    )
    args = parser.parse_args()

    pool_codes = tuple(args.pool_codes or DEFAULT_POOL_CODES)
    errors: list[dict[str, str]] = []
    pool_results: list[dict[str, Any]] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(pool_codes)) as executor:
        futures = {
            executor.submit(fetch_pool, pool_code, args.timeout, args.insecure): pool_code
            for pool_code in pool_codes
        }
        for future in concurrent.futures.as_completed(futures):
            pool_code = futures[future]
            try:
                pool_results.append(future.result())
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
                errors.append({"poolCode": pool_code, "error": str(exc)})

    output = {
        "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source": BASE_URL,
        "pool_codes": list(pool_codes),
        "errors": errors,
        "matches": merge_matches(pool_results),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2 if args.pretty else None))
    return 1 if errors and not pool_results else 0


if __name__ == "__main__":
    try:
        raise SystemExit(cli())
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        raise SystemExit(130)
