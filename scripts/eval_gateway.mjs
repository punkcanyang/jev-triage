#!/usr/bin/env node
/**
 * Live Gateway eval vs data/samples.jsonl → reports/eval-gateway-latest.md
 * Loads AI_GATEWAY_API_KEY from process env (or box-secrets via --load-card).
 * Never logs headers or keys.
 *
 * Usage:
 *   node scripts/eval_gateway.mjs --limit 30
 *   node scripts/eval_gateway.mjs --limit 100
 */
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { resolve, dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, "..");

function loadCard(name) {
  const p = process.env.BOX_SECRETS_JSON || "";
  try {
    const data = JSON.parse(readFileSync(p, "utf8"));
    const v = data?.card?.[name];
    if (typeof v === "string" && v.trim()) {
      process.env[name] = v.trim();
      return true;
    }
  } catch {
    /* ignore */
  }
  return false;
}

function parseArgs(argv) {
  let limit = 30;
  let out = join(ROOT, "reports", "eval-gateway-latest.md");
  let samples = join(ROOT, "data", "samples.jsonl");
  let loadSecrets = true;
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--limit" && argv[i + 1]) limit = Number(argv[++i]);
    else if (a === "--all") limit = null;
    else if (a === "--out" && argv[i + 1]) out = resolve(argv[++i]);
    else if (a === "--samples" && argv[i + 1]) samples = resolve(argv[++i]);
    else if (a === "--no-load-card") loadSecrets = false;
  }
  return { limit, out, samples, loadSecrets };
}

function loadSamples(path, limit) {
  const rows = [];
  for (const line of readFileSync(path, "utf8").split("\n")) {
    if (!line.trim()) continue;
    rows.push(JSON.parse(line));
    if (limit != null && rows.length >= limit) break;
  }
  return rows;
}

function nowCst() {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Shanghai",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  })
    .format(new Date())
    .replace(",", "") + " CST";
}

async function main() {
  const args = parseArgs(process.argv);
  if (args.loadSecrets) {
    const ok = loadCard("AI_GATEWAY_API_KEY");
    console.log("AI_GATEWAY_API_KEY loaded:", Boolean(ok && process.env.AI_GATEWAY_API_KEY));
  }
  if (!process.env.AI_GATEWAY_API_KEY?.trim()) {
    console.error(JSON.stringify({ error: "AI_GATEWAY_API_KEY missing", code: "GATEWAY_KEY_MISSING" }));
    process.exit(1);
  }

  const { classifyViaGateway } = await import(
    pathToFileURL(join(ROOT, "adapters/gateway/classify.mjs")).href
  );

  const rows = loadSamples(args.samples, args.limit);
  if (!rows.length) {
    console.error("no samples");
    process.exit(1);
  }

  const ACC_MIN = 0.8;
  const FA_MAX = 0.05;
  let queueCorrect = 0;
  let shouldReview = 0;
  let falseAuto = 0;
  let autoN = 0;
  let autoOk = 0;
  const details = [];
  let errors = 0;
  let firstError = null;

  for (const row of rows) {
    let pred;
    try {
      pred = await classifyViaGateway(row.text);
    } catch (e) {
      errors += 1;
      if (!firstError) firstError = String(e.message || e).slice(0, 240);
      details.push({
        id: row.id,
        gold_queue: row.queue,
        pred_queue: "ERROR",
        queue_ok: false,
        gold_needs_review: Boolean(row.needs_review),
        pred_needs_review: true,
        confidence: 0,
        error: true,
      });
      continue;
    }

    const qOk = pred.queue === row.queue;
    if (qOk) queueCorrect += 1;
    const goldNr = Boolean(row.needs_review);
    if (goldNr) {
      shouldReview += 1;
      if (!pred.needs_review) falseAuto += 1;
    }
    if (!pred.needs_review) {
      autoN += 1;
      if (qOk) autoOk += 1;
    }
    details.push({
      id: row.id,
      gold_queue: row.queue,
      pred_queue: pred.queue,
      queue_ok: qOk,
      gold_needs_review: goldNr,
      pred_needs_review: pred.needs_review,
      confidence: pred.confidence,
      refund_bool: pred.refund?.bool,
      via: pred.meta?.via,
    });
  }

  const n = rows.length;
  const overall = n ? queueCorrect / n : 0;
  const autoAcc = autoN ? autoOk / autoN : 0;
  const faRate = shouldReview ? falseAuto / shouldReview : 0;
  const passAcc = autoN > 0 && autoAcc >= ACC_MIN;
  const passFa = shouldReview === 0 || faRate <= FA_MAX;
  const blocked = errors === n;

  const lines = [
    `# Jev triage Gateway eval — ${nowCst()}`,
    "",
    `- mode: \`live/gateway\` (model \`typesafe-ai/jev\`, no Fast)`,
    `- samples: ${n} (file \`${args.samples.split("/").pop()}\`)`,
    `- errors: ${errors}/${n}${firstError ? ` (first: ${firstError.replace(/\|/g, "/")})` : ""}`,
    `- overall queue accuracy: **${(overall * 100).toFixed(1)}%** (${queueCorrect}/${n})`,
    `- auto-queue accuracy (pred needs_review=false): **${(autoAcc * 100).toFixed(1)}%** (${autoOk}/${autoN})`,
    `- false-auto rate (gold needs_review, pred auto): **${(faRate * 100).toFixed(1)}%** (${falseAuto}/${shouldReview})`,
    `- targets: auto-queue ≥ 80%; false-auto ≤ 5%; confidence < 0.55 → review`,
    "",
    "## Pass?",
    blocked
      ? "- **BLOCKED** — Gateway did not return usable classifications (see errors)."
      : [
          `- auto-queue accuracy ≥ 80%: ${passAcc ? "PASS" : "FAIL / n/a"}`,
          `- false-auto ≤ 5%: ${passFa ? "PASS" : "FAIL"}`,
          `- overall: ${passAcc && passFa ? "**PASS**" : "**FAIL**"}`,
        ].join("\n"),
    "",
    "## Notes",
    "- Adapter: `adapters/gateway/classify.mjs` (SDK `experimental_evaluate`, REST fallback).",
    "- Auth via `AI_GATEWAY_API_KEY` from env / optional BOX_SECRETS_JSON (never logged).",
    "- If errors mention credit card / customer_verification_required, add a card in Vercel AI Gateway to unlock credits.",
    "",
    "## Per-sample (abbrev)",
    "",
    "| id | gold | pred | ok | gold_nr | pred_nr | conf |",
    "|----|------|------|----|---------|---------|------|",
  ];

  for (const d of details.slice(0, 50)) {
    lines.push(
      `| ${d.id} | ${d.gold_queue} | ${d.pred_queue} | ${d.queue_ok ? "Y" : "N"} | ${d.gold_needs_review} | ${d.pred_needs_review} | ${(d.confidence ?? 0).toFixed(2)} |`
    );
  }
  if (details.length > 50) {
    lines.push(`| … | (${details.length - 50} more) | | | | | |`);
  }

  mkdirSync(dirname(args.out), { recursive: true });
  writeFileSync(args.out, lines.join("\n") + "\n", "utf8");
  console.log(`wrote ${args.out}`);
  console.log(
    `overall_queue_acc=${overall.toFixed(3)} auto_queue_acc=${autoAcc.toFixed(3)} false_auto=${faRate.toFixed(3)} n=${n} errors=${errors} blocked=${blocked} pass=${!blocked && passAcc && passFa}`
  );
  process.exit(blocked ? 2 : 0);
}

main().catch((e) => {
  console.error(JSON.stringify({ error: String(e.message || e).slice(0, 300) }));
  process.exit(1);
});
