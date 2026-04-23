from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Literal, Optional


Provider = Literal["openai", "anthropic", "stub"]


SYSTEM_PROMPT = """You are a privacy-safe email drafting assistant.

You will receive a user request containing special placeholder tokens like [[EMAIL_ADDRESS_1]] or <<PERSON_2>>.

CRITICAL RULES:
- Do NOT change, reformat, re-case, translate, split, merge, or remove ANY placeholder tokens.
- Copy placeholder tokens EXACTLY as-is, including brackets/angles/underscores and digits.
- If you need to mention a name/email/phone/invoice/NIC, you MUST use the placeholder token provided.

Write a professional email draft appropriate for business communication.
"""


@dataclass(frozen=True)
class LlmResponse:
    provider: Provider
    text: str


def _stub_email_draft(redacted_request: str) -> str:
    # Intentionally simple: proves round-trip token restoration without needing keys.
    # Try to reuse whatever tokens exist in the request so restoration is visible.
    tokens = re.findall(r"\[\[[A-Z_]+_\d+\]\]|\<\<[A-Z_]+_\d+\>\>", redacted_request)
    by_entity: dict[str, list[str]] = {}
    for t in tokens:
        inner = t.strip("<>[]")
        entity = inner.rsplit("_", 1)[0]
        by_entity.setdefault(entity, []).append(t)

    sender = (by_entity.get("PERSON") or ["[[PERSON_1]]"])[0]
    recipient = (by_entity.get("PERSON") or ["[[PERSON_2]]"])[1] if len(by_entity.get("PERSON") or []) > 1 else "[[PERSON_2]]"
    sender_email = (by_entity.get("EMAIL_ADDRESS") or ["[[EMAIL_ADDRESS_1]]"])[0]
    sender_phone = (by_entity.get("PHONE_NUMBER") or ["[[PHONE_NUMBER_1]]"])[0]
    invoice = (by_entity.get("INVOICE_NUMBER") or ["[[INVOICE_NUMBER_1]]"])[0]

    return (
        "Subject: Follow-up on overdue invoice\n\n"
        f"Hi {recipient},\n\n"
        f"I hope you’re doing well. I’m following up regarding the overdue invoice {invoice}.\n"
        "Could you please confirm the payment status and expected settlement date?\n\n"
        "If you need any supporting documents, please let me know and I’ll share them right away.\n\n"
        "Kind regards,\n"
        f"{sender}\n"
        f"{sender_email}\n"
        f"{sender_phone}\n\n"
        "----\n"
        "Original request (redacted):\n"
        f"{redacted_request}\n"
    )


def infer_provider() -> Provider:
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    return "stub"


def generate_email_draft(
    redacted_request: str,
    *,
    provider: Optional[Provider] = None,
    model: Optional[str] = None,
) -> LlmResponse:
    provider_inferred = provider or infer_provider()

    if provider_inferred == "openai":
        from openai import OpenAI

        client = OpenAI()
        chosen_model = model or os.getenv("OPENAI_MODEL") or "gpt-4.1-mini"
        resp = client.chat.completions.create(
            model=chosen_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": redacted_request},
            ],
            temperature=0.4,
        )
        return LlmResponse(provider="openai", text=resp.choices[0].message.content or "")

    if provider_inferred == "anthropic":
        from anthropic import Anthropic

        client = Anthropic()
        chosen_model = model or os.getenv("ANTHROPIC_MODEL") or "claude-3-5-sonnet-latest"
        resp = client.messages.create(
            model=chosen_model,
            max_tokens=700,
            temperature=0.4,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": redacted_request}],
        )
        text = ""
        for block in resp.content:
            # Anthropic returns structured content blocks
            if getattr(block, "type", None) == "text":
                text += getattr(block, "text", "")
        return LlmResponse(provider="anthropic", text=text)

    return LlmResponse(provider="stub", text=_stub_email_draft(redacted_request))

