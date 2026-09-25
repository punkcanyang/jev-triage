#!/usr/bin/env node
/**
 * Vercel AI Gateway adapter for Jev triage.
 *
 * Preferred: AI SDK experimental_evaluate + model typesafe-ai/jev
 * Fallback:  POST https://ai-gateway.vercel.sh/typesafe/v1/systemone (noul for refund/escalate)
 *
 * NEVER use *-fast or providerOptions.gateway.speed='fast'.
 * NEVER log Authorization headers or API keys.
 */

const QUEUES = {
  billing:
    "Charges, invoices, payments, subscriptions, double-charge, pricing, refunds as money issues, tax receipts.",
  account_access:
    "Login failures, password reset, 2FA/MFA, locked account, SSO, email change, unauthorized login.",
  product_bug:
    "Software/app/website defects, crashes, wrong data, feature broken, error messages, regressions.",
  shipping:
    "Order fulfillment, tracking, delayed/lost packages, wrong item shipped, address change before ship, warehouse.",
  general:
    "How-to questions, feature requests, feedback, unclear intent, other non-urgent support not matching a narrower queue.",
  abuse:
    "Harassment, fraud/scam reports, ToS violations, spam, threats, illegal content, safety emergencies.",
};

const URGENCY_CRITERIA = [
  "routine / informational, no time pressure",
  "mild inconvenience, can wait 1–2 business days",
  "moderate impact, wants same-day help",
  "high impact (money stuck, blocked from work), needs fast reply",
  "critical (safety, ongoing fraud, complete outage for many users)",
];

const QUEUE_NAMES = Object.keys(QUEUES);
const MIN_CONFIDENCE = Number(process.env.JEV_MIN_CONFIDENCE || 0.55);
const REST_URL =
  process.env.JEV_GATEWAY_REST_URL ||
  "https://ai-gateway.vercel.sh/typesafe/v1/systemone";

export function gatewayConfigured() {
  return Boolean(process.env.AI_GATEWAY_API_KEY && process.env.AI_GATEWAY_API_KEY.trim());
}

function noulPayload(noul, confidence = null) {
  if (noul == null || Number.isNaN(Number(noul))) {
    return { noul: null, bool: null, confidence };
  }
  const n = Number(noul);
  return {
    noul: n,
    bool: n >= 0.5,
    confidence: confidence != null ? Number(confidence) : null,
  };
}

function finalize({
  queue,
  urgency,
  refundNoul,
  escalateNoul,
  confidence,
  refundConf = null,
  escalateConf = null,
  queueProbabilities = null,
  backend = "gateway",
  model = null,
  via = "sdk",
}) {
  let needsReview = confidence < MIN_CONFIDENCE;
  if (
    refundNoul != null &&
    refundNoul >= 0.35 &&
    refundNoul <= 0.65 &&
    (refundConf ?? confidence) < 0.7
  ) {
    needsReview = true;
  }
  if (escalateNoul != null && escalateNoul >= 0.5 && confidence < 0.7) {
    needsReview = true;
  }

  const q = QUEUE_NAMES.includes(queue) ? queue : "general";
  const out = {
    queue: q,
    urgency: Math.max(0, Math.min(1, Number(urgency))),
    refund: noulPayload(refundNoul, refundConf),
    escalate: noulPayload(escalateNoul, escalateConf),
    confidence: Number(confidence),
    needs_review: Boolean(needsReview),
    meta: {
      backend,
      model,
      dry_run: false,
      min_confidence: MIN_CONFIDENCE,
      via,
    },
  };
  if (queueProbabilities) out.queue_probabilities = queueProbabilities;
  return out;
}

function sdkQuestions() {
  return {
    queue: {
      type: "choice",
      instructions:
        "Pick the single best customer-support queue for this ticket/email. Do not draft a reply. Prefer the narrowest accurate queue.",
      criteria: QUEUES,
    },
    urgency: {
      type: "score",
      instructions: "How urgent is a response for the customer?",
      criteria: URGENCY_CRITERIA,
    },
    refund: {
      type: "boolean",
      instructions:
        "Is the customer asking for or clearly entitled to a monetary refund/chargeback-style money return?",
      criteria: {
        true: "Customer wants or is entitled to money back.",
        false: "No monetary refund intent or entitlement.",
      },
    },
    escalate: {
      type: "boolean",
      instructions:
        "Should this be escalated to a senior agent/manager/legal/safety team (threats, fraud, legal, severe outage, VIP anger)?",
      criteria: {
        true: "Needs senior/legal/safety escalation.",
        false: "Frontline can handle.",
      },
    },
  };
}

function restQuestions() {
  // REST TypeSafe API uses "noul" instead of SDK "boolean"
  return {
    queue: {
      type: "choice",
      instructions:
        "Pick the single best customer-support queue for this ticket/email. Do not draft a reply. Prefer the narrowest accurate queue.",
      criteria: QUEUES,
    },
    urgency: {
      type: "score",
      instructions: "How urgent is a response for the customer?",
      criteria: URGENCY_CRITERIA,
    },
    refund: {
      type: "noul",
      instructions:
        "Is the customer asking for or clearly entitled to a monetary refund/chargeback-style money return? Yes = refund intent/entitlement.",
    },
    escalate: {
      type: "noul",
      instructions:
        "Should this be escalated to a senior agent/manager/legal/safety team (threats, fraud, legal, severe outage, VIP anger)?",
    },
  };
}

function normalizeScoreToUnit(score, nLevels) {
  if (score == null || Number.isNaN(Number(score))) return 0.5;
  const maxIdx = Math.max(1, nLevels - 1);
  return Math.max(0, Math.min(1, Number(score) / maxIdx));
}

function normalizeFromSdk(result, model) {
  const answers = result?.answers || {};
  const confMeta =
    result?.providerMetadata?.typesafe?.confidence ||
    result?.providerMetadata?.typesafeAI?.confidence ||
    {};

  const queueAns = answers.queue || {};
  const queue = queueAns.choice || "general";
  const queueProbs = queueAns.probabilities
    ? Object.fromEntries(
        Object.entries(queueAns.probabilities).map(([k, v]) => [k, Number(v)])
      )
    : null;
  const selectedProb =
    queueProbs && queue in queueProbs ? Number(queueProbs[queue]) : null;
  const queueConf =
    confMeta.queue != null
      ? Number(confMeta.queue)
      : selectedProb != null
        ? selectedProb
        : 0.5;

  const urgencyAns = answers.urgency || {};
  const urgency = normalizeScoreToUnit(urgencyAns.score, URGENCY_CRITERIA.length);

  const refundProb =
    answers.refund?.probability != null
      ? Number(answers.refund.probability)
      : answers.refund?.noul != null
        ? Number(answers.refund.noul)
        : null;
  const escalateProb =
    answers.escalate?.probability != null
      ? Number(answers.escalate.probability)
      : answers.escalate?.noul != null
        ? Number(answers.escalate.noul)
        : null;

  return finalize({
    queue,
    urgency,
    refundNoul: refundProb,
    escalateNoul: escalateProb,
    confidence: queueConf,
    refundConf: refundProb != null ? Math.max(refundProb, 1 - refundProb) : null,
    escalateConf:
      escalateProb != null ? Math.max(escalateProb, 1 - escalateProb) : null,
    queueProbabilities: queueProbs,
    backend: "gateway",
    model,
    via: "sdk",
  });
}

function normalizeFromRest(data, model) {
  // REST may nest under choices/scores/nouls or flat answers
  const choices = data?.choices || data?.answers || {};
  const scores = data?.scores || data?.answers || {};
  const nouls = data?.nouls || data?.answers || {};

  const choiceAns = choices.queue || data?.queue || {};
  const queue =
    typeof choiceAns === "string"
      ? choiceAns
      : choiceAns.choice || choiceAns.value || "general";
  const queueProbs = choiceAns.probabilities
    ? Object.fromEntries(
        Object.entries(choiceAns.probabilities).map(([k, v]) => [k, Number(v)])
      )
    : null;
  const queueConf =
    choiceAns.confidence != null
      ? Number(choiceAns.confidence)
      : queueProbs && queue in queueProbs
        ? Number(queueProbs[queue])
        : 0.5;

  const scoreAns = scores.urgency || data?.urgency || {};
  const rawScore =
    typeof scoreAns === "number" ? scoreAns : scoreAns.score ?? scoreAns.value;
  const urgency = normalizeScoreToUnit(rawScore, URGENCY_CRITERIA.length);

  const refundAns = nouls.refund || data?.refund || {};
  const escalateAns = nouls.escalate || data?.escalate || {};
  const refundNoul =
    typeof refundAns === "number"
      ? refundAns
      : refundAns.noul ?? refundAns.probability ?? null;
  const escalateNoul =
    typeof escalateAns === "number"
      ? escalateAns
      : escalateAns.noul ?? escalateAns.probability ?? null;

  return finalize({
    queue,
    urgency,
    refundNoul: refundNoul != null ? Number(refundNoul) : null,
    escalateNoul: escalateNoul != null ? Number(escalateNoul) : null,
    confidence: queueConf,
    refundConf:
      refundAns.confidence != null
        ? Number(refundAns.confidence)
        : refundNoul != null
          ? Math.max(Number(refundNoul), 1 - Number(refundNoul))
          : null,
    escalateConf:
      escalateAns.confidence != null
        ? Number(escalateAns.confidence)
        : escalateNoul != null
          ? Math.max(Number(escalateNoul), 1 - Number(escalateNoul))
          : null,
    queueProbabilities: queueProbs,
    backend: "gateway",
    model: data?.model || model,
    via: "rest",
  });
}

async function classifyViaSdk(text, model) {
  const { experimental_evaluate: evaluate } = await import("ai");
  const result = await evaluate({
    model,
    state: { body: text },
    questions: sdkQuestions(),
    // Do NOT set providerOptions.gateway.speed
    providerOptions: {
      gateway: { zeroDataRetention: true },
    },
  });
  return normalizeFromSdk(result, model);
}

async function classifyViaRest(text, model) {
  const key = process.env.AI_GATEWAY_API_KEY?.trim();
  if (!key) {
    const err = new Error("AI_GATEWAY_API_KEY missing for REST fallback");
    err.code = "GATEWAY_KEY_MISSING";
    throw err;
  }

  const res = await fetch(REST_URL, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${key}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model,
      state: { body: text },
      questions: restQuestions(),
    }),
  });

  const bodyText = await res.text();
  let data;
  try {
    data = JSON.parse(bodyText);
  } catch {
    data = { raw: bodyText.slice(0, 500) };
  }

  if (!res.ok) {
    const err = new Error(
      `Gateway REST ${res.status}: ${typeof data?.error === "string" ? data.error : data?.message || res.statusText}`
    );
    err.code = "GATEWAY_REST_ERROR";
    err.status = res.status;
    // never attach headers or key
    throw err;
  }

  return normalizeFromRest(data, model);
}

/**
 * @param {string} text
 * @returns {Promise<object>}
 */
export async function classifyViaGateway(text) {
  if (!gatewayConfigured()) {
    const err = new Error(
      "AI_GATEWAY_API_KEY missing. Use Python TypeSafe path or dry-run. Do not invent keys."
    );
    err.code = "GATEWAY_KEY_MISSING";
    throw err;
  }

  const model = process.env.JEV_GATEWAY_MODEL || "typesafe-ai/jev";
  if (/fast/i.test(model)) {
    throw new Error(`Refusing fast model slug: ${model}`);
  }

  try {
    return await classifyViaSdk(text, model);
  } catch (sdkErr) {
    // Prefer REST with noul if SDK fails (boolean mapping / auth / etc.)
    try {
      const out = await classifyViaRest(text, model);
      out.meta = {
        ...out.meta,
        sdk_error: String(sdkErr?.message || sdkErr).slice(0, 200),
      };
      return out;
    } catch (restErr) {
      const err = new Error(
        `Gateway SDK and REST failed. sdk=${String(sdkErr?.message || sdkErr).slice(0, 160)}; rest=${String(restErr?.message || restErr).slice(0, 160)}`
      );
      err.code = "GATEWAY_BOTH_FAILED";
      throw err;
    }
  }
}

// CLI
if (process.argv[1]?.endsWith("classify.mjs")) {
  const check = process.argv.includes("--check");
  if (check) {
    console.log(
      JSON.stringify(
        {
          gatewayConfigured: gatewayConfigured(),
          model: process.env.JEV_GATEWAY_MODEL || "typesafe-ai/jev",
          restHint: REST_URL,
          minConfidence: MIN_CONFIDENCE,
        },
        null,
        2
      )
    );
    process.exit(0);
  }
  const text = process.argv
    .slice(2)
    .filter((a) => !a.startsWith("--"))
    .join(" ")
    .trim();
  if (!text) {
    console.error('Usage: node classify.mjs --check | node classify.mjs "ticket text"');
    process.exit(2);
  }
  classifyViaGateway(text)
    .then((r) => {
      // omit raw blobs; print contract only
      const { meta, ...rest } = r;
      console.log(JSON.stringify({ ...rest, meta }, null, 2));
    })
    .catch((e) => {
      console.error(JSON.stringify({ error: e.message, code: e.code || null }));
      process.exit(1);
    });
}
