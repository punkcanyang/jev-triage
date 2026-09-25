# Jev triage eval — 2026-09-21 09:09 CST

- mode: `live/typesafe`
- samples: 20 (file `samples.jsonl`)
- overall queue accuracy: **90.0%** (18/20)
- auto-queue accuracy (pred needs_review=false): **100.0%** (12/12)
- false-auto rate (gold needs_review, pred auto): **0.0%** (0/4)
- targets: auto-queue ≥ 80%; false-auto ≤ 5%; confidence < 0.85 → review

## Pass?
- auto-queue accuracy ≥ 80%: PASS
- false-auto ≤ 5%: PASS

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
| s0004 | account_access | general | N | True | True | 0.86 |
| s0005 | product_bug | product_bug | Y | False | False | 1.00 |
| s0006 | product_bug | product_bug | Y | False | False | 0.95 |
| s0007 | shipping | shipping | Y | False | False | 1.00 |
| s0008 | shipping | shipping | Y | False | False | 1.00 |
| s0009 | general | general | Y | False | False | 0.91 |
| s0010 | general | product_bug | N | True | True | 0.97 |
| s0011 | abuse | abuse | Y | False | True | 0.94 |
| s0012 | abuse | abuse | Y | True | True | 1.00 |
| s0013 | billing | billing | Y | False | True | 0.85 |
| s0014 | shipping | shipping | Y | False | True | 0.85 |
| s0015 | billing | billing | Y | False | False | 1.00 |
| s0016 | billing | billing | Y | False | False | 1.00 |
| s0017 | account_access | account_access | Y | False | False | 0.97 |
| s0018 | account_access | account_access | Y | True | True | 0.46 |
| s0019 | product_bug | product_bug | Y | False | True | 1.00 |
| s0020 | product_bug | product_bug | Y | False | False | 0.99 |
