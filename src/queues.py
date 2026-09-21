"""Fixed CS queues for triage (document in README)."""

from __future__ import annotations

QUEUES: dict[str, str] = {
    "billing": (
        "Charges, invoices, payments, subscriptions, double-charge, "
        "pricing, refunds as money issues, tax receipts."
    ),
    "account_access": (
        "Login failures, password reset, 2FA/MFA, locked account, "
        "SSO, email change, unauthorized login."
    ),
    "product_bug": (
        "Software/app/website defects, crashes, wrong data, feature "
        "broken, error messages, regressions."
    ),
    "shipping": (
        "Order fulfillment, tracking, delayed/lost packages, wrong "
        "item shipped, address change before ship, warehouse."
    ),
    "general": (
        "How-to questions, feature requests, feedback, unclear intent, "
        "other non-urgent support not matching a narrower queue."
    ),
    "abuse": (
        "Harassment, fraud/scam reports, ToS violations, spam, "
        "threats, illegal content, safety emergencies."
    ),
}

QUEUE_NAMES = tuple(QUEUES.keys())

URGENCY_CRITERIA = [
    "routine / informational, no time pressure",
    "mild inconvenience, can wait 1–2 business days",
    "moderate impact, wants same-day help",
    "high impact (money stuck, blocked from work), needs fast reply",
    "critical (safety, ongoing fraud, complete outage for many users)",
]
