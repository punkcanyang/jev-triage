# Gateway adapter (stub)

Activates when `AI_GATEWAY_API_KEY` is set on the box.

- Model: `typesafe-ai/jev` (or `typesafe-ai/jev-latest`) — **never** `*-fast` / `speed:'fast'`
- SDK: Node `ai` ≥ 7.0.105 `experimental_evaluate`
- Auth: `Authorization: Bearer $AI_GATEWAY_API_KEY`
- REST: `https://ai-gateway.vercel.sh/typesafe` → `POST /typesafe/v1/systemone`
- Docs: https://vercel.com/kb/guide/typesafe-jev-and-ai-sdk

Until the key exists, use Python:

```bash
/workspace/tools/typesafe-venv/bin/python scripts/classify_cli.py --live "..."
```

Check stub status:

```bash
node adapters/gateway/classify.mjs --check
```
