"""Command-line entry point for the canonical I Ching engine."""

from __future__ import annotations

import argparse
import json

from .advice import generate_advice, render_reading
from .iching import resolve_casts


def main() -> None:
    parser = argparse.ArgumentParser(description="Resolve an I Ching casting.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--casts",
        nargs=6,
        type=int,
        metavar=("C1", "C2", "C3", "C4", "C5", "C6"),
        help="Six canonical values: 6, 7, 8, or 9; bottom to top.",
    )
    group.add_argument(
        "--coin-totals",
        nargs=6,
        type=int,
        metavar=("R1", "R2", "R3", "R4", "R5", "R6"),
        help="Six three-coin roll totals: each total must be 6, 7, 8, or 9.",
    )
    parser.add_argument("--question", help="Question to answer from the reading.")
    parser.add_argument("--language", choices=("ko", "en"), default="ko")
    parser.add_argument("--advice", action="store_true", help="Generate DeepSeek advice.")
    parser.add_argument("--json", action="store_true", help="Print raw JSON instead of readable text.")
    args = parser.parse_args()
    try:
        result = (
            resolve_casts(args.casts)
            if args.casts is not None
            else resolve_casts(args.coin_totals)
        )
        if args.advice:
            if not args.question:
                parser.error("--advice requires --question.")
            result["advice"] = generate_advice(result, args.question, args.language)
    except (TypeError, ValueError, KeyError, RuntimeError) as error:
        parser.error(str(error))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_reading(result, result.get("advice")))


if __name__ == "__main__":
    main()
