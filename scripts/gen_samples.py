#!/usr/bin/env python3
"""Generate ≥200 synthetic+public-style labeled support tickets (desensitized)."""

from __future__ import annotations

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "samples.jsonl"

QUEUES = [
    "billing",
    "account_access",
    "product_bug",
    "shipping",
    "general",
    "abuse",
]

# Templates: (queue, urgency 0-1, refund bool, escalate bool, needs_review, texts[])
TEMPLATES: list[tuple] = [
    (
        "billing",
        0.7,
        True,
        False,
        False,
        [
            "I was charged twice for my September subscription. Please refund the duplicate charge. Order ref ORD-{n}.",
            "我的信用卡被重复扣款了，请退还多收的一次费用。账单号 INV-{n}。",
            "Invoice #{n} shows the wrong amount. I need a corrected invoice and a refund for the overcharge.",
            "Cancel my plan and refund the unused portion. Charged on the 1st.",
            "Payment failed but you still billed me. Refund ASAP. Last four {n}.",
            "订阅续费了我没同意，要求退款。",
            "Double charge on Mastercard for Pro plan — money back please.",
            "Tax invoice missing for payment {n}; also overcharged shipping fee.",
        ],
    ),
    (
        "billing",
        0.4,
        False,
        False,
        False,
        [
            "Can you explain the line items on invoice INV-{n}?",
            "请问你们的年付和月付差价怎么算？",
            "Where do I download past receipts?",
            "Is sales tax included in the listed price?",
        ],
    ),
    (
        "account_access",
        0.75,
        False,
        False,
        False,
        [
            "I cannot log in — password reset emails never arrive. Account: user{n}@example.com",
            "账号被锁定了，提示尝试次数过多，请帮忙解锁。",
            "Lost my phone; need to reset 2FA for workspace {n}.",
            "SSO with Google suddenly fails with error invalid_grant.",
            "Someone changed my email; I can't access the account. Help.",
            "登录一直转圈，密码确定没错。",
            "MFA codes are rejected even though the clock is synced.",
            "Please disable SMS 2FA and switch to authenticator app.",
        ],
    ),
    (
        "account_access",
        0.35,
        False,
        False,
        True,
        [
            "How do I add a teammate to my org?",
            "请问如何修改绑定的手机号？步骤发一下就行。",
            "Is passkey login supported on Linux?",
        ],
    ),
    (
        "product_bug",
        0.8,
        False,
        False,
        False,
        [
            "App crashes every time I open the reports tab on iOS 18. Stack: null pointer #{n}.",
            "后台保存后数据丢失，刷新变回旧版本。严重 bug。",
            "Dashboard shows 500 Internal Server Error since this morning.",
            "Export CSV truncates columns after the 10th field — regression after v2.{n}.",
            "Search returns no results for known SKUs; worked yesterday.",
            "白屏，控制台报 TypeError cannot read properties of undefined.",
            "Webhook deliveries stuck in 'pending' for 6 hours.",
            "Mobile app freezes on upload > 20MB.",
        ],
    ),
    (
        "product_bug",
        0.45,
        False,
        False,
        False,
        [
            "Minor UI glitch: button label overflow on German locale.",
            "Dark mode contrast on secondary buttons is low.",
            "Typo in the onboarding checklist.",
        ],
    ),
    (
        "shipping",
        0.7,
        False,
        False,
        False,
        [
            "Tracking {n} stuck at 'in transit' for 9 days. Where is my package?",
            "快递显示已签收但我没收到，请查丢件。运单 {n}。",
            "Wrong item shipped — ordered blue, got red. Order ORD-{n}.",
            "Please change shipping address before it leaves the warehouse.",
            "Package arrived damaged; need replacement shipment.",
            "物流信息三天没更新了，着急用。",
            "Can you split shipment? Need SKU-A sooner.",
            "Customs hold on international parcel — need commercial invoice copy.",
        ],
    ),
    (
        "shipping",
        0.3,
        False,
        False,
        False,
        [
            "What are your shipping carriers to Canada?",
            "发货一般需要几天？普通件即可。",
            "Do you offer weekend delivery?",
        ],
    ),
    (
        "general",
        0.25,
        False,
        False,
        False,
        [
            "How do I export my data for a personal backup?",
            "请问有没有学生优惠？",
            "Feature request: keyboard shortcut for bulk archive.",
            "Thanks for the last fix — just saying hi.",
            "Where is the API rate limit documented?",
            "想了解一下企业版和专业版的区别。",
            "Can I change the display language to 中文?",
            "Is there a status page for incidents?",
        ],
    ),
    (
        "general",
        0.5,
        False,
        False,
        True,
        [
            "Not sure if this is billing or a bug — my balance looks wrong after a deploy.",
            "有点奇怪，功能能用但数字对不上，不知道找谁。",
            "Something feels off with my account; maybe permissions?",
        ],
    ),
    (
        "abuse",
        0.9,
        False,
        True,
        False,
        [
            "User spam-bots are flooding our form with phishing links. Please ban ASN {n}.",
            "有人用你们的平台骚扰我，附聊天记录，请立刻处理。",
            "Reporting scam storefront impersonating our brand.",
            "Threats received via in-app DM — safety concern.",
            "This account is selling illegal goods; ToS violation.",
            "举报：疑似诈骗群在滥用邀请链接。",
            "Harassment campaign against our staff profiles.",
            "Credential stuffing attempts from IP block {n}.x — please block.",
        ],
    ),
    (
        "abuse",
        0.6,
        False,
        True,
        True,
        [
            "Possible ToS issue? Competitor left a rude review.",
            "不确定算不算违规，对方一直发广告私信。",
        ],
    ),
    # Cross-pressure / high review cases
    (
        "billing",
        0.95,
        True,
        True,
        False,
        [
            "If I don't get a full refund today I will contact my lawyer and the BBB. Charge ID {n}.",
            "再不退款我就投诉到消协和媒体。订单 {n}。",
        ],
    ),
    (
        "shipping",
        0.85,
        True,
        False,
        False,
        [
            "Package never arrived — I want a refund not a reship. Tracking {n}.",
            "丢件了，不要补发，直接退款。运单 {n}。",
        ],
    ),
]


def urgency_bin(u: float) -> str:
    if u < 0.33:
        return "low"
    if u < 0.66:
        return "mid"
    return "high"


def main() -> None:
    rng = random.Random(42)
    rows: list[dict] = []
    i = 0
    # Repeat templates with variation until ≥220
    while len(rows) < 220:
        for queue, urg, refund, escalate, needs_review, texts in TEMPLATES:
            text = rng.choice(texts).format(n=1000 + (i % 9000))
            # light paraphrase noise
            if rng.random() < 0.3:
                text = text + (" Thanks." if rng.random() < 0.5 else " 谢谢。")
            rows.append(
                {
                    "id": f"s{len(rows)+1:04d}",
                    "text": text,
                    "queue": queue,
                    "urgency": round(urg + rng.uniform(-0.05, 0.05), 3),
                    "urgency_bin": urgency_bin(urg),
                    "refund": refund,
                    "escalate": escalate,
                    "needs_review": needs_review,
                    "lang": "zh" if any("\u4e00" <= c <= "\u9fff" for c in text) else "en",
                }
            )
            i += 1
            if len(rows) >= 220:
                break

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {len(rows)} → {OUT}")


if __name__ == "__main__":
    main()
