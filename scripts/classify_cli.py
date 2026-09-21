#!/usr/bin/env python3
"""Classify ticket/email text → JSON (stdin or args). No reply drafting."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.classify import classify, load_config  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Jev triage classify → JSON only")
    p.add_argument("text", nargs="?", help="Ticket/email body (or pass via stdin)")
    p.add_argument("--dry-run", action="store_true", help="Heuristic only (no API)")
    p.add_argument(
        "--live",
        action="store_true",
        help="Force TypeSafe system_one (needs TYPESAFE_API_KEY)",
    )
    p.add_argument(
        "--backend",
        choices=("typesafe", "gateway", "dry"),
        default=None,
        help="Override config backend",
    )
    args = p.parse_args(argv)

    text = args.text
    if text is None:
        if sys.stdin.isatty():
            p.error("provide text arg or pipe stdin")
        text = sys.stdin.read()

    cfg = load_config()
    dry = True if args.dry_run else (False if args.live else None)
    backend = args.backend
    if args.live and backend is None:
        backend = "typesafe"
    if args.dry_run and backend is None:
        backend = "dry"

    try:
        result = classify(text, dry_run=dry, backend=backend, config=cfg)
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False), file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
