# Jev triage Gateway eval — 2026-09-21 09:06 CST

- mode: `live/gateway` (model `typesafe-ai/jev`, no Fast)
- samples: 30 (file `samples.jsonl`)
- errors: 30/30 (first: Gateway SDK and REST failed. sdk=AI Gateway requires a valid credit card on file to service requests. Please visit https://vercel.com/d?to=%2F%5Bteam%5D%2F%7E%2Fai%3Fmodal%3Dadd-credit-card to ; rest=Gateway REST 403: Forbidden)
- overall queue accuracy: **0.0%** (0/30)
- auto-queue accuracy (pred needs_review=false): **0.0%** (0/0)
- false-auto rate (gold needs_review, pred auto): **0.0%** (0/0)
- targets: auto-queue ≥ 80%; false-auto ≤ 5%; confidence < 0.55 → review

## Pass?
- **BLOCKED** — Gateway did not return usable classifications (see errors).

## Notes
- Adapter: `adapters/gateway/classify.mjs` (SDK `experimental_evaluate`, REST fallback).
- Auth via `AI_GATEWAY_API_KEY` from env (never logged).
- If errors mention credit card / customer_verification_required, add a card in Vercel AI Gateway to unlock credits.

## Per-sample (abbrev)

| id | gold | pred | ok | gold_nr | pred_nr | conf |
|----|------|------|----|---------|---------|------|
| s0001 | billing | ERROR | N | false | true | 0.00 |
| s0002 | billing | ERROR | N | false | true | 0.00 |
| s0003 | account_access | ERROR | N | false | true | 0.00 |
| s0004 | account_access | ERROR | N | true | true | 0.00 |
| s0005 | product_bug | ERROR | N | false | true | 0.00 |
| s0006 | product_bug | ERROR | N | false | true | 0.00 |
| s0007 | shipping | ERROR | N | false | true | 0.00 |
| s0008 | shipping | ERROR | N | false | true | 0.00 |
| s0009 | general | ERROR | N | false | true | 0.00 |
| s0010 | general | ERROR | N | true | true | 0.00 |
| s0011 | abuse | ERROR | N | false | true | 0.00 |
| s0012 | abuse | ERROR | N | true | true | 0.00 |
| s0013 | billing | ERROR | N | false | true | 0.00 |
| s0014 | shipping | ERROR | N | false | true | 0.00 |
| s0015 | billing | ERROR | N | false | true | 0.00 |
| s0016 | billing | ERROR | N | false | true | 0.00 |
| s0017 | account_access | ERROR | N | false | true | 0.00 |
| s0018 | account_access | ERROR | N | true | true | 0.00 |
| s0019 | product_bug | ERROR | N | false | true | 0.00 |
| s0020 | product_bug | ERROR | N | false | true | 0.00 |
| s0021 | shipping | ERROR | N | false | true | 0.00 |
| s0022 | shipping | ERROR | N | false | true | 0.00 |
| s0023 | general | ERROR | N | false | true | 0.00 |
| s0024 | general | ERROR | N | true | true | 0.00 |
| s0025 | abuse | ERROR | N | false | true | 0.00 |
| s0026 | abuse | ERROR | N | true | true | 0.00 |
| s0027 | billing | ERROR | N | false | true | 0.00 |
| s0028 | shipping | ERROR | N | false | true | 0.00 |
| s0029 | billing | ERROR | N | false | true | 0.00 |
| s0030 | billing | ERROR | N | false | true | 0.00 |
