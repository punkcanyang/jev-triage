# Jev triage eval — 2026-09-21 09:13 CST

- mode: `dry/heuristic`
- samples: 220 (file `samples.jsonl`)
- overall queue accuracy: **81.4%** (179/220)
- auto-queue accuracy (pred needs_review=false): **84.2%** (80/95)
- false-auto rate (gold needs_review, pred auto): **0.0%** (0/47)
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
| s0001 | billing | billing | Y | False | False | 0.95 |
| s0002 | billing | billing | Y | False | False | 0.95 |
| s0003 | account_access | account_access | Y | False | False | 0.95 |
| s0004 | account_access | general | N | True | True | 0.50 |
| s0005 | product_bug | product_bug | Y | False | False | 0.95 |
| s0006 | product_bug | general | N | False | True | 0.50 |
| s0007 | shipping | shipping | Y | False | False | 0.95 |
| s0008 | shipping | shipping | Y | False | True | 0.50 |
| s0009 | general | general | Y | False | True | 0.50 |
| s0010 | general | general | Y | True | True | 0.42 |
| s0011 | abuse | general | N | False | False | 0.95 |
| s0012 | abuse | abuse | Y | True | True | 0.42 |
| s0013 | billing | billing | Y | False | True | 0.95 |
| s0014 | shipping | shipping | Y | False | True | 0.81 |
| s0015 | billing | billing | Y | False | False | 0.95 |
| s0016 | billing | billing | Y | False | False | 0.95 |
| s0017 | account_access | account_access | Y | False | False | 0.95 |
| s0018 | account_access | account_access | Y | True | True | 0.50 |
| s0019 | product_bug | product_bug | Y | False | False | 0.95 |
| s0020 | product_bug | general | N | False | True | 0.50 |
| s0021 | shipping | shipping | Y | False | False | 0.95 |
| s0022 | shipping | shipping | Y | False | False | 0.95 |
| s0023 | general | general | Y | False | False | 0.95 |
| s0024 | general | general | Y | True | True | 0.42 |
| s0025 | abuse | abuse | Y | False | True | 0.95 |
| s0026 | abuse | abuse | Y | True | True | 0.42 |
| s0027 | billing | billing | Y | False | True | 0.95 |
| s0028 | shipping | shipping | Y | False | True | 0.81 |
| s0029 | billing | billing | Y | False | False | 0.95 |
| s0030 | billing | billing | Y | False | False | 0.95 |
| s0031 | account_access | account_access | Y | False | False | 0.95 |
| s0032 | account_access | general | N | True | True | 0.50 |
| s0033 | product_bug | general | N | False | False | 0.95 |
| s0034 | product_bug | product_bug | Y | False | False | 0.95 |
| s0035 | shipping | shipping | Y | False | False | 0.95 |
| s0036 | shipping | shipping | Y | False | True | 0.50 |
| s0037 | general | general | Y | False | False | 0.95 |
| s0038 | general | general | Y | True | True | 0.42 |
| s0039 | abuse | abuse | Y | False | True | 0.95 |
| s0040 | abuse | abuse | Y | True | True | 0.42 |
| s0041 | billing | billing | Y | False | True | 0.95 |
| s0042 | shipping | shipping | Y | False | True | 0.81 |
| s0043 | billing | billing | Y | False | True | 0.95 |
| s0044 | billing | billing | Y | False | False | 0.95 |
| s0045 | account_access | account_access | Y | False | False | 0.95 |
| s0046 | account_access | general | N | True | True | 0.50 |
| s0047 | product_bug | product_bug | Y | False | False | 0.95 |
| s0048 | product_bug | general | N | False | True | 0.50 |
| s0049 | shipping | shipping | Y | False | False | 0.95 |
| s0050 | shipping | shipping | Y | False | False | 0.95 |
| … | (170 more) | | | | | |
