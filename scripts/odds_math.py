#!/usr/bin/env python3
"""Small odds helpers for Jingsai analysis.

The script intentionally uses only the Python standard library so it can run in
Claude Code, Codex, and most local shells without installing dependencies.
"""

from __future__ import annotations

import argparse
import json
from typing import Iterable


def parse_float(value: str | float | int | None) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number <= 0:
        return None
    return number


def implied_probability(odds: float) -> float:
    return 1.0 / odds


def normalize_probabilities(probabilities: Iterable[float]) -> list[float]:
    values = list(probabilities)
    total = sum(values)
    if total <= 0:
        return [0.0 for _ in values]
    return [value / total for value in values]


def fair_odds(probability: float) -> float | None:
    if probability <= 0:
        return None
    return 1.0 / probability


def expected_value(probability: float, odds: float) -> float:
    return probability * odds - 1.0


def analyze_market(odds: list[float]) -> dict:
    implied = [implied_probability(odd) for odd in odds]
    normalized = normalize_probabilities(implied)
    overround = sum(implied) - 1.0
    return {
        "odds": odds,
        "implied_probabilities": implied,
        "no_vig_probabilities": normalized,
        "fair_odds_no_vig": [fair_odds(prob) for prob in normalized],
        "overround": overround,
        "payout_rate_estimate": 1.0 / sum(implied) if sum(implied) > 0 else None,
    }


def cli() -> int:
    parser = argparse.ArgumentParser(description="Convert odds to probabilities and rough EV.")
    parser.add_argument(
        "--odds",
        nargs="+",
        required=True,
        help="Decimal odds, for example: --odds 1.80 3.40 4.20",
    )
    parser.add_argument(
        "--my-probs",
        nargs="*",
        help="Optional estimated probabilities aligned with odds, for example: --my-probs 0.55 0.27 0.18",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args()

    odds = [parse_float(value) for value in args.odds]
    if any(value is None for value in odds):
        parser.error("--odds must contain positive numbers")
    odds_values = [value for value in odds if value is not None]

    result = analyze_market(odds_values)

    if args.my_probs:
        my_probs = [parse_float(value) for value in args.my_probs]
        if any(value is None for value in my_probs):
            parser.error("--my-probs must contain positive numbers")
        if len(my_probs) != len(odds_values):
            parser.error("--my-probs must have the same length as --odds")
        prob_values = [value for value in my_probs if value is not None]
        result["my_probabilities"] = prob_values
        result["my_fair_odds"] = [fair_odds(prob) for prob in prob_values]
        result["expected_values"] = [
            expected_value(probability, odd)
            for probability, odd in zip(prob_values, odds_values, strict=True)
        ]

    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
