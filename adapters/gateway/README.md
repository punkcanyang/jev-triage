# Gateway adapter (live)

Activates when `AI_GATEWAY_API_KEY` is set in the environment (never print).

- Model: `typesafe-ai/jev` — **never** `*-fast` / `speed:'fast'`
- SDK: Node `ai` ≥ 7.0.105 `experimental_evaluate` with `state` + typed questions
- Auth: `Authorization: Bearer $AI_GATEWAY_API_KEY` (SDK reads env; REST sets Bearer)
- REST fallback: `POST https://ai-gateway.vercel.sh/typesafe/v1/systemone` (uses `noul` for refund/escalate)
- Output contract matches Python `src/classify.py`
- Docs: https://vercel.com/kb/guide/typesafe-jev-and-ai-sdk

```bash
export PATH="$HOME/.local/node/current/bin:$PATH"
cd adapters/gateway && npm install   # ai ≥ 7.0.105
node classify.mjs --check
node classify.mjs "I was charged twice, please refund."
# batch eval from repo root:
node ../../scripts/eval_gateway.mjs --limit 30
```

If calls return `customer_verification_required` / credit-card message, add a card in Vercel AI Gateway to unlock free credits. Models list may still work while `systemone` is blocked.
