#!/usr/bin/env node
/**
 * Gateway adapter stub for Jev triage.
 *
 * Preferred when AI_GATEWAY_API_KEY exists:
 *   - Vercel AI SDK `ai` ≥ 7.0.105 `experimental_evaluate`
 *   - model: typesafe-ai/jev  (NOT *-fast; do NOT set speed:'fast')
 *   - Auth: Bearer AI_GATEWAY_API_KEY
 *   - REST fallback: POST https://ai-gateway.vercel.sh/typesafe/v1/systemone
 *
 * Docs: https://vercel.com/kb/guide/typesafe-jev-and-ai-sdk
 *
 * Until the key is present this module refuses to call the network.
 * Python src/classify.py (TypeSafe SDK) remains the working smoke path.
 */

const QUEUES = {
  billing: "Charges, invoices, payments, subscriptions, refunds as money issues.",
  account_access: "Login, password, 2FA, locked account, SSO.",
  product_bug: "Software defects, crashes, regressions, errors.",
  shipping: "Fulfillment, tracking, lost/wrong packages.",
  general: "How-to, feature requests, unclear non-urgent support.",
  abuse: "Harassment, fraud, ToS, safety.",
};

const URGENCY_CRITERIA = [
  "routine / informational",
  "mild inconvenience",
  "moderate impact, same-day",
  "high impact, money/work blocked",
  "critical safety/fraud/outage",
];

export function gatewayConfigured() {
  return Boolean(process.env.AI_GATEWAY_API_KEY && process.env.AI_GATEWAY_API_KEY.trim());
}

/**
 * @param {string} text
 * @returns {Promise<object>}
 */
export async function classifyViaGateway(text) {
  if (!gatewayConfigured()) {
    const err = new Error(
      "AI_GATEWAY_API_KEY missing. Use Python TypeSafe path (TYPESAFE_API_KEY) or dry-run. " +
        "Do not invent keys."
    );
    err.code = "GATEWAY_KEY_MISSING";
    throw err;
  }

  // Lazy import so `node classify.mjs --check` works without node_modules when key absent.
  const { experimental_evaluate } = await import("ai");

  // NO Fast: model must stay typesafe-ai/jev (or jev-latest) — never *-fast / speed:'fast'
  const model = process.env.JEV_GATEWAY_MODEL || "typesafe-ai/jev";
  if (/fast/i.test(model)) {
    throw new Error(`Refusing fast model slug: ${model}`);
  }

  // Shape mirrors TypeSafe questions: choice + score + boolean(noul)
  const result = await experimental_evaluate({
    model,
    prompt: text,
    // Exact API surface may follow Vercel KB; keep criteria aligned with Python queues.
    questions: {
      queue: {
        type: "choice",
        instructions: "Best CS queue; do not draft a reply.",
        criteria: QUEUES,
      },
      urgency: {
        type: "score",
        instructions: "Urgency of response",
        criteria: URGENCY_CRITERIA,
      },
      refund: {
        type: "boolean",
        instructions: "Customer wants/entitled to monetary refund?",
      },
      escalate: {
        type: "boolean",
        instructions: "Escalate to senior/legal/safety?",
      },
    },
  });

  // Normalize to the same JSON contract as Python classify()
  // (field names depend on SDK result — stub leaves mapping TODO when key arrives)
  return {
    queue: result?.queue ?? result?.choices?.queue ?? null,
    urgency: result?.urgency ?? result?.scores?.urgency ?? null,
    refund: result?.refund ?? result?.booleans?.refund ?? null,
    escalate: result?.escalate ?? result?.booleans?.escalate ?? null,
    confidence: result?.confidence ?? null,
    needs_review: null,
    meta: {
      backend: "gateway",
      model,
      dry_run: false,
      stub_normalize: true,
      note: "Wire result mapping against live Gateway response when key is available",
    },
    raw: result,
  };
}

// CLI
const isMain = process.argv[1] && import.meta.url.endsWith(process.argv[1].replace(/\\/g, "/"))
  || process.argv[1]?.endsWith("classify.mjs");

if (process.argv[1]?.endsWith("classify.mjs")) {
  const check = process.argv.includes("--check");
  if (check) {
    console.log(
      JSON.stringify(
        {
          gatewayConfigured: gatewayConfigured(),
          model: process.env.JEV_GATEWAY_MODEL || "typesafe-ai/jev",
          restHint: "POST https://ai-gateway.vercel.sh/typesafe/v1/systemone",
        },
        null,
        2
      )
    );
    process.exit(0);
  }
  const text = process.argv.slice(2).filter((a) => !a.startsWith("--")).join(" ") || "";
  if (!text) {
    console.error("Usage: node classify.mjs --check | node classify.mjs \"ticket text\"");
    process.exit(2);
  }
  classifyViaGateway(text)
    .then((r) => {
      console.log(JSON.stringify(r, null, 2));
    })
    .catch((e) => {
      console.error(JSON.stringify({ error: e.message, code: e.code || null }));
      process.exit(1);
    });
}
