#!/usr/bin/env python3
"""
Eval classifier vs labeled samples → reports/eval-latest.md

Default: dry/heuristic smoke (small limit).
Full 200 live:  python scripts/eval.py --live --limit 200
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.classify import classify, load_config  # noqa: E402

SAMPLES = ROOT / "data" / "samples.jsonl"
REPORT = ROOT / "reports" / "eval-latest.md"
TZ = ZoneInfo("Asia/Shanghai")


def load_samples(path: Path, limit: int | None) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
            if limit is not None and len(rows) >= limit:
                break
    return rows


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Eval triage classifier vs labels")
    p.add_argument("--samples", type=Path, default=SAMPLES)
    p.add_argument("--limit", type=int, default=20, help="Max samples (default 20 smoke)")
    p.add_argument("--all", action="store_true", help="Use all samples (overrides --limit)")
    p.add_argument("--dry-run", action="store_true", default=None, help="Force heuristic")
    p.add_argument("--live", action="store_true", help="Force TypeSafe live API")
    p.add_argument("--out", type=Path, default=REPORT)
    args = p.parse_args(argv)

    limit = None if args.all else args.limit
    rows = load_samples(args.samples, limit)
    if not rows:
        print(f"no samples in {args.samples}", file=sys.stderr)
        return 1

    cfg = load_config()
    dry = True
    backend = "dry"
    if args.live:
        dry = False
        backend = "typesafe"
    elif args.dry_run:
        dry = True
        backend = "dry"

    n = len(rows)
    queue_correct = 0
    # false-auto: gold needs_review=True but model needs_review=False
    should_review = 0
    false_auto = 0
    auto_and_queued = 0
    auto_queue_correct = 0
    details = []

    for row in rows:
        pred = classify(row["text"], dry_run=dry, backend=backend, config=cfg)
        gold_q = row["queue"]
        pred_q = pred["queue"]
        q_ok = pred_q == gold_q
        if q_ok:
            queue_correct += 1

        gold_nr = bool(row.get("needs_review"))
        # Also treat high-stakes gold refund/escalate as should-review if model auto'd wrongly
        # Spec: false-auto on should-review ≤5%
        if gold_nr:
            should_review += 1
            if not pred["needs_review"]:
                false_auto += 1

        if not pred["needs_review"]:
            auto_and_queued += 1
            if q_ok:
                auto_queue_correct += 1

        details.append(
            {
                "id": row.get("id"),
                "gold_queue": gold_q,
                "pred_queue": pred_q,
                "queue_ok": q_ok,
                "gold_needs_review": gold_nr,
                "pred_needs_review": pred["needs_review"],
                "confidence": pred["confidence"],
            }
        )

    overall_acc = queue_correct / n if n else 0.0
    auto_acc = (auto_queue_correct / auto_and_queued) if auto_and_queued else 0.0
    false_auto_rate = (false_auto / should_review) if should_review else 0.0

    targets = cfg.get("thresholds") or {}
    acc_min = float(targets.get("auto_queue_accuracy_min", 0.80))
    fa_max = float(targets.get("false_auto_max", 0.05))

    now = datetime.now(TZ).strftime("%Y-%m-%d %H:%M CST")
    mode = "live/typesafe" if not dry else "dry/heuristic"

    lines = [
        f"# Jev triage eval — {now}",
        "",
        f"- mode: `{mode}`",
        f"- samples: {n} (file `{args.samples.name}`)",
        f"- overall queue accuracy: **{overall_acc:.1%}** ({queue_correct}/{n})",
        f"- auto-queue accuracy (pred needs_review=false): **{auto_acc:.1%}** "
        f"({auto_queue_correct}/{auto_and_queued})",
        f"- false-auto rate (gold needs_review, pred auto): **{false_auto_rate:.1%}** "
        f"({false_auto}/{should_review})",
        f"- targets: auto-queue ≥ {acc_min:.0%}; false-auto ≤ {fa_max:.0%}; "
        f"confidence < {cfg['thresholds']['min_confidence']} → review",
        "",
        "## Pass?",
        f"- auto-queue accuracy ≥ {acc_min:.0%}: "
        f"{'PASS' if auto_acc >= acc_min else 'FAIL / n/a'}",
        f"- false-auto ≤ {fa_max:.0%}: "
        f"{'PASS' if (should_review == 0 or false_auto_rate <= fa_max) else 'FAIL'}",
        "",
        "## Notes",
        "- Dry mode uses keyword heuristics (offline). Live uses TypeSafe `system_one`.",
        "- Full set: `python scripts/eval.py --all --dry-run` or `--live --limit 200`.",
        "- Gateway path blocked until `AI_GATEWAY_API_KEY` is set (see README).",
        "",
        "## Per-sample (abbrev)",
        "",
        "| id | gold | pred | ok | gold_nr | pred_nr | conf |",
        "|----|------|------|----|---------|---------|------|",
    ]
    for d in details[:50]:
        lines.append(
            f"| {d['id']} | {d['gold_queue']} | {d['pred_queue']} | "
            f"{'Y' if d['queue_ok'] else 'N'} | {d['gold_needs_review']} | "
            f"{d['pred_needs_review']} | {d['confidence']:.2f} |"
        )
    if len(details) > 50:
        lines.append(f"| … | ({len(details) - 50} more) | | | | | |")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {args.out}")
    print(f"overall_queue_acc={overall_acc:.3f} auto_queue_acc={auto_acc:.3f} "
          f"false_auto={false_auto_rate:.3f} n={n} mode={mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
