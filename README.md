# Jev triage MVP (ticket / email → JSON)

Local demo under `/workspace/saas-scout/jev-triage`. **Classify only** — no customer reply drafting, no buyer LLM keys.

Grok session: `01a0c168-c41a-7761-aff2-c04fc8d64065` (title `jev-triage`). Resume: `grok --resume 01a0c168-c41a-7761-aff2-c04fc8d64065` or `grok -c`. **No Fast.**

## Queues (fixed 6)

| queue | when |
|-------|------|
| `billing` | charges, invoices, subscriptions, money refunds |
| `account_access` | login, password, 2FA, locked account, SSO |
| `product_bug` | crashes, defects, regressions, errors |
| `shipping` | tracking, lost/wrong packages, fulfillment |
| `general` | how-to, feature requests, unclear non-urgent |
| `abuse` | harassment, fraud, ToS, safety |

## Output JSON

```json
{
  "queue": "billing",
  "urgency": 0.72,
  "refund": { "noul": 0.88, "bool": true, "confidence": 0.9 },
  "escalate": { "noul": 0.12, "bool": false, "confidence": 0.8 },
  "confidence": 0.81,
  "needs_review": false
}
```

## Thresholds (acceptance)

| metric | target |
|--------|--------|
| Auto-queue accuracy (among `needs_review=false`) | ≥ **80%** |
| False-auto (gold `needs_review=true` but model auto) | ≤ **5%** |
| Low confidence | `confidence` **&lt; 0.55** → `needs_review=true` |

## Backends

| backend | when | notes |
|---------|------|-------|
| **TypeSafe Python SDK** `system_one` | `TYPESAFE_API_KEY` set (current box) | Working smoke path; venv `/workspace/tools/typesafe-venv` |
| **Vercel AI Gateway** | `AI_GATEWAY_API_KEY` set | **MISSING now** — stub in `adapters/gateway/`; model `typesafe-ai/jev` only (no Fast) |
| **dry / heuristic** | `--dry-run` or no key | Offline keyword classifier for eval smoke |

**Gateway blocker:** do not invent keys. When key arrives: Node `ai` ≥7.0.105 `experimental_evaluate`, Bearer auth, optional REST `POST https://ai-gateway.vercel.sh/typesafe/v1/systemone`. See https://vercel.com/kb/guide/typesafe-jev-and-ai-sdk

## Setup

```bash
export PATH="/workspace/tools/typesafe-venv/bin:$HOME/.local/node/current/bin:$HOME/.local/bin:$PATH"
cd /workspace/saas-scout/jev-triage
# TYPESAFE_API_KEY must be in env for --live (never print it)
```

## Classify

```bash
# dry
python scripts/classify_cli.py --dry-run "I was charged twice, please refund."

# live TypeSafe
python scripts/classify_cli.py --live "I was charged twice, please refund."

# stdin
echo "无法登录，密码重置邮件收不到" | python scripts/classify_cli.py --dry-run
```

## Eval

```bash
# smoke (default limit 20, dry)
python scripts/eval.py --dry-run --limit 20

# full 200+ dry
python scripts/eval.py --all --dry-run

# live smoke / full (API cost)
python scripts/eval.py --live --limit 10
python scripts/eval.py --live --limit 200
```

Report: `reports/eval-latest.md`

## Samples

`data/samples.jsonl` — ≥200 synthetic+public-style CN/EN tickets with human labels:
`queue`, `urgency` / `urgency_bin`, `refund`, `escalate`, `needs_review`. Desensitized.

Regenerate: `python scripts/gen_samples.py`

## Layout

```
config.yaml
src/classify.py          # classify(text) → dict
scripts/classify_cli.py
scripts/eval.py
scripts/gen_samples.py
data/samples.jsonl
reports/eval-latest.md
adapters/gateway/        # Node stub (key missing)
TASK.md
```

## Not in scope

Auto-replies, Zendesk, collecting ChatGPT/Claude keys, public repo, Fast models.
