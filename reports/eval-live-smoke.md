# Jev triage eval — 2026-09-21 08:42 CST

- mode: `live/typesafe`
- samples: 5 (file `samples.jsonl`)
- overall queue accuracy: **80.0%** (4/5)
- auto-queue accuracy (pred needs_review=false): **80.0%** (4/5)
- false-auto rate (gold needs_review, pred auto): **100.0%** (1/1)
- targets: auto-queue ≥ 80%; false-auto ≤ 5%; confidence < 0.55 → review

## Pass?
- auto-queue accuracy ≥ 80%: PASS
- false-auto ≤ 5%: FAIL

## Notes
- Dry mode uses keyword heuristics (offline). Live uses TypeSafe `system_one`.
- Full set: `python scripts/eval.py --all --dry-run` or `--live --limit 200`.
- Gateway path blocked until `AI_GATEWAY_API_KEY` is set (see README).

## Per-sample (abbrev)

| id | gold | pred | ok | gold_nr | pred_nr | conf |
|----|------|------|----|---------|---------|------|
| s0001 | billing | billing | Y | False | False | 1.00 |
| s0002 | billing | billing | Y | False | False | 1.00 |
| s0003 | account_access | account_access | Y | False | False | 1.00 |
| s0004 | account_access | general | N | True | False | 0.88 |
| s0005 | product_bug | product_bug | Y | False | False | 1.00 |
