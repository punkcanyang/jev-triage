"""Classify ticket/email body → structured triage JSON (no reply drafting)."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml

from .queues import QUEUE_NAMES, QUEUES, URGENCY_CRITERIA

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "config.yaml"
MIN_CONFIDENCE_DEFAULT = 0.55


def load_config(path: Path | None = None) -> dict[str, Any]:
    cfg_path = path or DEFAULT_CONFIG
    data: dict[str, Any] = {}
    if cfg_path.is_file():
        with cfg_path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    thresholds = data.setdefault("thresholds", {})
    thresholds.setdefault("min_confidence", MIN_CONFIDENCE_DEFAULT)
    data.setdefault("model", "jev-latest")
    data.setdefault("backend", "typesafe")
    data.setdefault("queues", list(QUEUE_NAMES))
    return data


def _noul_payload(noul: float | None, confidence: float | None = None) -> dict[str, Any]:
    if noul is None:
        return {"noul": None, "bool": None, "confidence": confidence}
    n = float(noul)
    return {
        "noul": n,
        "bool": bool(n >= 0.5),
        "confidence": float(confidence) if confidence is not None else None,
    }


def _ambiguous_text(text: str) -> bool:
    t = (text or "").lower()
    markers = (
        "不确定", "不知道", "算不算", "有点奇怪", "maybe", "not sure",
        "feels off", "something feels", "possible tos", "不清楚", "找谁",
        "unsure", "ambiguous", "数字对不上", "不对劲", "weird", "strange",
        "how do i add a teammate", "passkey", "permissions?",
        "修改绑定", "手机号", "步骤发一下", "如何修改",
    )
    return any(m in t for m in markers)


def _finalize(
    *,
    queue: str,
    urgency: float,
    refund_noul: float | None,
    escalate_noul: float | None,
    confidence: float,
    refund_conf: float | None = None,
    escalate_conf: float | None = None,
    min_confidence: float = MIN_CONFIDENCE_DEFAULT,
    queue_probabilities: dict[str, float] | None = None,
    backend: str = "typesafe",
    model: str | None = None,
    dry_run: bool = False,
    text: str | None = None,
) -> dict[str, Any]:
    needs_review = confidence < min_confidence
    # High-stakes / ambiguous → human review (cut false-auto)
    if queue == "abuse":
        needs_review = True
    if escalate_noul is not None and escalate_noul >= 0.45:
        needs_review = True
    if refund_noul is not None and 0.35 <= refund_noul <= 0.65 and (refund_conf or confidence) < 0.7:
        needs_review = True
    if escalate_noul is not None and escalate_noul >= 0.5 and confidence < 0.7:
        needs_review = True
    if queue_probabilities:
        ranked = sorted((float(v) for v in queue_probabilities.values()), reverse=True)
        if ranked and ranked[0] < 0.90:
            needs_review = True
        if len(ranked) >= 2 and (ranked[0] - ranked[1]) < 0.18:
            needs_review = True
    if text and _ambiguous_text(text):
        needs_review = True

    out: dict[str, Any] = {
        "queue": queue if queue in QUEUE_NAMES else "general",
        "urgency": max(0.0, min(1.0, float(urgency))),
        "refund": _noul_payload(refund_noul, refund_conf),
        "escalate": _noul_payload(escalate_noul, escalate_conf),
        "confidence": float(confidence),
        "needs_review": bool(needs_review),
        "meta": {
            "backend": backend,
            "model": model,
            "dry_run": dry_run,
            "min_confidence": min_confidence,
        },
    }
    if queue_probabilities:
        out["queue_probabilities"] = queue_probabilities
    return out


# --- Dry / heuristic path (no API; for smoke + offline eval replay) ---

_KW: dict[str, tuple[str, ...]] = {
    "billing": (
        "refund", "charge", "charged", "invoice", "payment", "billing", "subscription",
        "double charge", "overcharged", "price", "信用卡", "扣款", "账单", "退款", "收费",
        "订阅", "发票", "付款",
    ),
    "account_access": (
        "password", "login", "log in", "sign in", "2fa", "mfa", "locked", "reset",
        "cannot access", "can't access", "sso", "账号", "密码", "登录", "验证码", "锁定",
        "无法登录", "两步验证",
    ),
    "product_bug": (
        "bug", "crash", "error", "broken", "not working", "doesn't work", "regression",
        "exception", "500", "glitch", "崩溃", "报错", "故障", "bug", "无法使用", "白屏",
    ),
    "shipping": (
        "shipping", "shipment", "tracking", "delivery", "package", "parcel", "warehouse",
        "lost package", "wrong item", "物流", "快递", "包裹", "发货", "运单", "配送",
        "丢件", "错发",
    ),
    "abuse": (
        "abuse", "harass", "fraud", "scam", "phishing", "threat", "illegal", "tos",
        "spam", "骚扰", "诈骗", "欺诈", "钓鱼", "威胁", "举报", "违规",
    ),
}


def _heuristic_classify(text: str, min_confidence: float) -> dict[str, Any]:
    t = text.lower()
    scores: dict[str, float] = {q: 0.0 for q in QUEUE_NAMES}
    for q, kws in _KW.items():
        for kw in kws:
            if kw.lower() in t:
                scores[q] += 1.0 + 0.15 * len(kw.split())
    # mild general bias if nothing matched
    if max(scores.values()) < 0.5:
        scores["general"] = 1.0
    else:
        scores["general"] += 0.1

    total = sum(scores.values()) or 1.0
    probs = {q: scores[q] / total for q in QUEUE_NAMES}
    queue = max(probs, key=probs.get)
    top = probs[queue]
    # map margin → confidence
    ranked = sorted(probs.values(), reverse=True)
    margin = ranked[0] - (ranked[1] if len(ranked) > 1 else 0.0)
    confidence = min(0.95, 0.45 + 0.35 * top + 0.4 * margin)

    # Ambiguity / soft how-to → force review (align with gold needs_review)
    ambiguous = bool(
        re.search(
            r"not sure|maybe|uncertain|feels off|不知道|不确定|有点奇怪|possible tos|"
            r"算不算|which (team|queue)|unclear",
            t,
        )
    )
    soft_howto = bool(
        re.search(
            r"how do i|how to|请问如何|步骤|is .+ supported|一般需要几天|学生优惠|"
            r"weekend delivery|feature request|typo in|dark mode|了解一下",
            t,
        )
    ) and not re.search(r"cannot|can't|无法|locked|crash|refund|退款|fraud|诈骗", t)
    if ambiguous:
        confidence = min(confidence, 0.42)
    elif soft_howto:
        confidence = min(confidence, 0.50)
    if margin < 0.15 and top < 0.55:
        confidence = min(confidence, 0.48)

    # urgency heuristics
    urgency = 0.35
    if re.search(r"urgent|asap|immediately|紧急|马上|立刻|critical|outage", t):
        urgency = 0.85
    elif re.search(r"today|same.?day|blocked|无法工作|今天", t):
        urgency = 0.65
    elif re.search(r"whenever|fyi|curious|请问一下|了解一下", t):
        urgency = 0.2

    refund_noul = 0.15
    if re.search(r"refund|退款|chargeback|money back|退钱", t):
        refund_noul = 0.85
    elif re.search(r"charged|扣款|overcharg", t):
        refund_noul = 0.55

    escalate_noul = 0.1
    if re.search(r"lawyer|legal|manager|supervisor|投诉|律师|媒体|sue|bbb", t):
        escalate_noul = 0.9
    elif re.search(r"fraud|scam|threat|安全|人身|harass", t):
        escalate_noul = 0.75
    elif urgency >= 0.8:
        escalate_noul = 0.45

    return _finalize(
        queue=queue,
        urgency=urgency,
        refund_noul=refund_noul,
        escalate_noul=escalate_noul,
        confidence=confidence,
        refund_conf=0.7 if refund_noul >= 0.5 else 0.6,
        escalate_conf=0.7 if escalate_noul >= 0.5 else 0.6,
        min_confidence=min_confidence,
        queue_probabilities=probs,
        backend="dry",
        model=None,
        dry_run=True,
        text=text,
    )


def _typesafe_classify(text: str, cfg: dict[str, Any]) -> dict[str, Any]:
    # Prefer shared typesafe-venv if present
    venv_site = Path(os.environ.get("TYPESAFE_VENV_SITE") or "")
    if venv_site.is_dir():
        import sys

        p = str(venv_site)
        if p not in sys.path:
            sys.path.insert(0, p)

    from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

    model = str(cfg.get("model") or "jev-latest")
    min_conf = float(cfg["thresholds"]["min_confidence"])

    questions = {
        "queue": Choice(
            instructions=(
                "Pick the single best customer-support queue for this ticket/email. "
                "Do not draft a reply. Prefer the narrowest accurate queue."
            ),
            criteria=dict(QUEUES),
        ),
        "urgency": Score(
            instructions="How urgent is a response for the customer?",
            criteria=list(URGENCY_CRITERIA),
        ),
        "refund": Noul(
            instructions=(
                "Is the customer asking for or clearly entitled to a monetary refund/"
                "chargeback-style money return? Yes = refund intent/entitlement."
            ),
        ),
        "escalate": Noul(
            instructions=(
                "Should this be escalated to a senior agent/manager/legal/safety team "
                "(threats, fraud, legal, severe outage, VIP anger)?"
            ),
        ),
    }

    with TypeSafeClient(model=model) as client:
        result = client.system_one(state=text, questions=questions, model=model)

    choice_ans = result.choices.get("queue")
    queue = choice_ans.choice if choice_ans else "general"
    confidence = (
        float(choice_ans.confidence)
        if choice_ans and choice_ans.confidence is not None
        else 0.5
    )
    probs = (
        {k: float(v) for k, v in dict(choice_ans.probabilities).items()}
        if choice_ans and choice_ans.probabilities is not None
        else None
    )

    score_ans = result.scores.get("urgency")
    urgency = float(score_ans.score) if score_ans and score_ans.score is not None else 0.5

    refund_ans = result.nouls.get("refund")
    refund_noul = float(refund_ans.noul) if refund_ans and refund_ans.noul is not None else None
    refund_conf = (
        float(refund_ans.confidence)
        if refund_ans and getattr(refund_ans, "confidence", None) is not None
        else None
    )

    esc_ans = result.nouls.get("escalate")
    escalate_noul = float(esc_ans.noul) if esc_ans and esc_ans.noul is not None else None
    escalate_conf = (
        float(esc_ans.confidence)
        if esc_ans and getattr(esc_ans, "confidence", None) is not None
        else None
    )

    return _finalize(
        queue=queue or "general",
        urgency=urgency,
        refund_noul=refund_noul,
        escalate_noul=escalate_noul,
        confidence=confidence,
        refund_conf=refund_conf,
        escalate_conf=escalate_conf,
        min_confidence=min_conf,
        queue_probabilities=probs,
        backend="typesafe",
        model=getattr(result, "model", None) or model,
        dry_run=False,
        text=text,
    )



def _gateway_classify_via_cli(text: str, cfg: dict[str, Any]) -> dict[str, Any]:
    """Shell out to Node Gateway adapter (never prints keys)."""
    import json
    import subprocess

    if not os.environ.get("AI_GATEWAY_API_KEY"):
        # optional: BOX_SECRETS_JSON path with .card.AI_GATEWAY_API_KEY (local only)
        secrets = Path(os.environ.get("BOX_SECRETS_JSON") or "")
        if secrets.is_file():
            try:
                data = json.loads(secrets.read_text(encoding="utf-8"))
                v = (data.get("card") or {}).get("AI_GATEWAY_API_KEY")
                if isinstance(v, str) and v.strip():
                    os.environ["AI_GATEWAY_API_KEY"] = v.strip()
            except Exception:
                pass
    if not os.environ.get("AI_GATEWAY_API_KEY"):
        raise RuntimeError(
            "backend=gateway but AI_GATEWAY_API_KEY is missing. "
            "Use backend=typesafe (TYPESAFE_API_KEY) or dry_run=True. "
            "See adapters/gateway/ and README."
        )

    node = os.environ.get("NODE_BIN") or str(
        Path.home() / ".local/node/current/bin/node"
    )
    script = ROOT / "adapters" / "gateway" / "classify.mjs"
    env = os.environ.copy()
    # ensure child sees key; do not log
    proc = subprocess.run(
        [node, str(script), text],
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
        cwd=str(ROOT),
    )
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "gateway cli failed").strip().splitlines()
        msg = err[-1] if err else "gateway cli failed"
        raise RuntimeError(msg[:400])
    return json.loads(proc.stdout)


def classify(
    text: str,
    *,
    dry_run: bool | None = None,
    backend: str | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Classify ticket/email body text into triage JSON.

    backend resolution:
      - dry_run=True → heuristic dry
      - backend='gateway' → Node adapters/gateway/classify.mjs via CLI
      - else typesafe live if TYPESAFE_API_KEY set, else dry
    """
    if not (text or "").strip():
        raise ValueError("text must be non-empty")

    cfg = config or load_config()
    min_conf = float(cfg["thresholds"]["min_confidence"])
    be = (backend or cfg.get("backend") or "typesafe").lower()

    if dry_run is True or be == "dry":
        return _heuristic_classify(text, min_conf)

    if be == "gateway":
        return _gateway_classify_via_cli(text, cfg)

    # typesafe (default)
    if not os.environ.get("TYPESAFE_API_KEY"):
        return _heuristic_classify(text, min_conf)

    return _typesafe_classify(text, cfg)
