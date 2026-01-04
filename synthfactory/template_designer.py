from __future__ import annotations

import json
import random
from dataclasses import dataclass
from typing import Optional, List, Tuple

from .llm_client import LLMClient
from .llm_factory import create_llm_client


@dataclass(frozen=True)
class Design:
    doc_type: str
    letter_template: Optional[str]
    logo_position: str
    base_font: str
    mono_font: str


class TemplateDesigner:
    def __init__(
        self,
        *,
        enabled: bool = True,
        provider: str = "ollama",
        llm_client: Optional[LLMClient] = None,
    ):
        self.enabled = bool(enabled)
        self._base_fonts = ["Helvetica", "Times-Roman"]
        self._mono_fonts = ["Courier"]

        if llm_client:
            self._llm_client = llm_client
        elif enabled:
            self._llm_client = create_llm_client(provider=provider)
        else:
            self._llm_client = None

    def _random(self, allowed_letter_templates: List[str]) -> Design:
        doc_type = "statement" if random.random() < 0.5 else "letter"
        tpl = (
            random.choice(allowed_letter_templates)
            if allowed_letter_templates
            else None
        )
        return Design(
            doc_type=doc_type,
            letter_template=tpl if doc_type == "letter" else None,
            logo_position=random.choice(["left", "center", "right"]),
            base_font=random.choice(self._base_fonts),
            mono_font=random.choice(self._mono_fonts),
        )

    def _keyword_route(
        self, prompt: str, allowed_letter_templates: List[str]
    ) -> Tuple[Optional[str], Optional[str]]:
        p = (prompt or "").lower()

        def pick(t: str) -> Optional[str]:
            if not allowed_letter_templates:
                return t
            return (
                t
                if t in allowed_letter_templates
                else (allowed_letter_templates[0] if allowed_letter_templates else None)
            )

        if any(
            k in p
            for k in (
                "shipping",
                "delivery",
                "depot",
                "warehouse",
                "logistics",
                "dispatch",
            )
        ):
            return "letter", pick("shipping_schedule")
        if any(
            k in p
            for k in ("appointment", "clinic", "healthcare", "hospital", "checkup")
        ):
            return "letter", pick("appointment_notice")
        if any(k in p for k in ("invoice", "bill", "billing", "payment due")):
            return "letter", pick("invoice_summary")
        if any(
            k in p
            for k in (
                "utilities",
                "outage",
                "service change",
                "service changes",
                "maintenance window",
                "planned works",
            )
        ):
            return "letter", pick("service_change_notice")
        if any(k in p for k in ("policy", "renewal", "insurance")):
            return "letter", pick("policy_renewal_notice")

        if any(
            k in p
            for k in (
                "statement",
                "transactions",
                "balance",
                "account statement",
                "sort code",
                "direct debit",
                "overdraft",
            )
        ):
            return "statement", None

        return None, None

    def next(self, prompt: str, allowed_letter_templates: List[str]) -> Design:
        prompt = (prompt or "").strip()
        allowed_letter_templates = list(allowed_letter_templates or [])

        if (not prompt) or (not self.enabled) or not self._llm_client:
            routed_type, routed_tpl = self._keyword_route(
                prompt, allowed_letter_templates
            )
            if routed_type:
                base = self._random(allowed_letter_templates)
                return Design(
                    doc_type=routed_type,
                    letter_template=routed_tpl if routed_type == "letter" else None,
                    logo_position=base.logo_position,
                    base_font=base.base_font,
                    mono_font=base.mono_font,
                )
            return self._random(allowed_letter_templates)

        sys = (
            "You choose a document type and (if letter) a template. "
            "Return STRICT JSON with keys: doc_type, letter_template, logo_position, base_font, mono_font. "
            "doc_type must be 'statement' or 'letter'. "
            "logo_position must be 'left','center','right'. "
            f"Allowed letter_template values: {allowed_letter_templates or ['(any)']}."
        )
        user = f"Context: {prompt}"

        try:
            data = self._llm_client.generate(sys + "\n" + user)
            obj = data if isinstance(data, dict) else {}
        except Exception:
            obj = {}

        doc_type = obj.get("doc_type") or "letter"
        if doc_type not in ("statement", "letter"):
            doc_type = "letter"

        tpl = obj.get("letter_template")
        if doc_type == "statement":
            tpl = None
        else:
            if allowed_letter_templates:
                if tpl not in allowed_letter_templates:
                    tpl = random.choice(allowed_letter_templates)
            else:
                tpl = tpl or "service_change_notice"

        logo_position = obj.get("logo_position") or random.choice(
            ["left", "center", "right"]
        )
        if logo_position not in ("left", "center", "right"):
            logo_position = random.choice(["left", "center", "right"])

        base_font = obj.get("base_font") or random.choice(self._base_fonts)
        if base_font not in self._base_fonts:
            base_font = random.choice(self._base_fonts)

        mono_font = obj.get("mono_font") or "Courier"
        if mono_font not in self._mono_fonts:
            mono_font = "Courier"

        return Design(
            doc_type=doc_type,
            letter_template=tpl,
            logo_position=logo_position,
            base_font=base_font,
            mono_font=mono_font,
        )
