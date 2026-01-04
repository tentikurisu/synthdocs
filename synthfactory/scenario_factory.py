from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass
from typing import Optional

from .llm_client import LLMClient
from .llm_factory import create_llm_client

LOGO_STYLES = ("nb_bars", "c_circle", "h_wave", "a_triangle", "s_slash")
HEADER_ALIGNMENTS = ("left", "center", "right")


@dataclass(frozen=True)
class Scenario:
    industry: str
    company_name: str
    accent_rgb: tuple[int, int, int]
    logo_style: str
    paper_tint_rgb: tuple[int, int, int] | None
    header_alignment: str


class ScenarioFactory:
    def __init__(
        self,
        *,
        enabled: bool = True,
        provider: str = "ollama",
        llm_client: Optional[LLMClient] = None,
        rng: Optional[random.Random] = None,
    ):
        self.enabled = bool(enabled)
        self.rng = rng or random.Random()
        self._company_pool = [
            "Harbourlight",
            "Northbridge",
            "Cedar",
            "Amberline",
            "Slatefield",
            "Pinkstone",
            "Yellowfin",
            "Rivermark",
            "Coppergate",
            "Moonharbor",
            "Juniperworks",
            "Kingsway",
            "Skyforge",
            "Oakridge",
            "Seabrook",
            "Bracken & Co",
            "Lumenfield",
            "Greywharf",
            "Primrose",
            "Ironleaf",
            "Foxmere",
            "Stonehaven",
            "Willowgate",
            "Brightmarsh",
            "Westridge",
            "Crownfield",
            "Seacrest",
            "Maplebridge",
        ]
        self._industries = [
            "banking",
            "construction",
            "utilities",
            "insurance",
            "healthcare",
            "telecoms",
            "retail",
            "logistics",
            "education",
            "property",
        ]
        self._suffixes = [
            "Ltd",
            "Group",
            "Services",
            "Holdings",
            "Partners",
            "Co",
            "Associates",
        ]
        self._paper_tints = [
            (250, 236, 240),
            (244, 244, 230),
            (235, 245, 255),
            (255, 245, 230),
            (240, 240, 240),
        ]

        if llm_client:
            self._llm_client = llm_client
        elif enabled:
            self._llm_client = create_llm_client(provider=provider)
        else:
            self._llm_client = None

    def next(self, prompt: str | None) -> Scenario:
        prompt = (prompt or "").strip()
        if (not self.enabled) or (not prompt) or not self._llm_client:
            return self._random_scenario()

        variation_hint = f"variation_seed={self.rng.randint(0, 10_000_000)}"

        sys = """Return ONLY strict JSON with keys:
industry, company_name, accent_rgb (array of 3 ints 0-255),
logo_style (nb_bars|c_circle|h_wave|a_triangle|s_slash),
paper_tint_rgb (array of 3 ints or null),
header_alignment (left|center|right).

Rules:
- Fictional company only; DO NOT use real banks/brands.
- If the user specifies company name / colours / alignment, respect it.
- If not specified, RANDOMISE per document (do not stick to one default style).
"""

        llm_prompt = (
            sys + "\n\nUser context:\n" + prompt + "\n" + variation_hint + "\n\nJSON:"
        )
        data = self._llm_client.generate(llm_prompt)

        if not data:
            return self._random_scenario()
        return self._coerce(data, fallback=self._random_scenario())

    def _random_scenario(self) -> Scenario:
        name = self.rng.choice(self._company_pool)
        industry = self.rng.choice(self._industries)
        suffix = self.rng.choice(self._suffixes)
        company_name = f"{name} {suffix} (Synthetic)"
        accent_rgb = (
            self.rng.randint(10, 245),
            self.rng.randint(10, 245),
            self.rng.randint(10, 245),
        )
        logo_style = self.rng.choice(LOGO_STYLES)
        header_alignment = self.rng.choice(HEADER_ALIGNMENTS)
        paper_tint_rgb = (
            self.rng.choice(self._paper_tints) if (self.rng.random() < 0.35) else None
        )
        return Scenario(
            industry,
            company_name,
            accent_rgb,
            logo_style,
            paper_tint_rgb,
            header_alignment,
        )

    def _coerce(self, data: dict, fallback: Scenario) -> Scenario:
        def rgb_tuple(v, fb):
            if isinstance(v, list) and len(v) == 3:
                try:
                    return (int(v[0]) % 256, int(v[1]) % 256, int(v[2]) % 256)
                except Exception:
                    return fb
            return fb

        industry = str(data.get("industry", fallback.industry))[:40]
        company_name = str(data.get("company_name", fallback.company_name))[:80]
        accent_rgb = rgb_tuple(data.get("accent_rgb"), fallback.accent_rgb)

        logo_style = str(data.get("logo_style", fallback.logo_style))
        if logo_style not in LOGO_STYLES:
            logo_style = fallback.logo_style

        header_alignment = str(data.get("header_alignment", fallback.header_alignment))
        if header_alignment not in HEADER_ALIGNMENTS:
            header_alignment = fallback.header_alignment

        tint = data.get("paper_tint_rgb", None)
        if tint is None:
            paper_tint_rgb = fallback.paper_tint_rgb
        else:
            paper_tint_rgb = rgb_tuple(tint, fallback.paper_tint_rgb)

        return Scenario(
            industry,
            company_name,
            accent_rgb,
            logo_style,
            paper_tint_rgb,
            header_alignment,
        )
