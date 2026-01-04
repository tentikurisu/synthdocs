from __future__ import annotations

import random
from pathlib import Path

from .config import AppCfg
from .faker_gen import make_statement, make_letter
from .scenario_factory import ScenarioFactory
from .template_designer import TemplateDesigner
from .models import GroundTruth, GroundTruthField
from .branding import Theme
from .render_pdf import render_statement_pdf, render_letter_pdf
from .render_jpg import render_statement_pages_jpg, render_letter_jpg
from .noise import apply_noise_pipeline
from .llm_factory import create_llm_client


def _visibility_flags(doc_type: str) -> dict[str, bool]:
    base = {
        "owner_address_lines": random.random() > 0.10,
        "owner_postcode": random.random() > 0.08,
        "sort_code": random.random() > 0.08,
        "account_number": random.random() > 0.10,
        "period": random.random() > 0.05,
        "opening_balance": random.random() > 0.05,
        "closing_balance": random.random() > 0.05,
        "transactions": True,
    }
    if doc_type == "letter":
        base["transactions"] = False
    return base


def _looks_non_financial(prompt: str) -> bool:
    lower = (prompt or "").lower()
    if not lower.strip():
        return False

    non_fin = (
        "shipping",
        "manifest",
        "delivery",
        "depot",
        "warehouse",
        "logistics",
        "dispatch",
        "route",
        "appointment",
        "clinic",
        "hospital",
        "healthcare",
        "prescription",
        "utilities",
        "outage",
        "maintenance",
        "service change",
        "construction",
        "site",
        "project",
        "quote",
        "consultancy",
        "invoice",
        "purchase order",
        "work order",
        "cloud",
        "saas",
        "subscription",
        "billing notice",
    )
    fin = (
        "statement",
        "transactions",
        "balance",
        "account",
        "sort code",
        "overdraft",
        "direct debit",
        "mortgage",
        "loan arrears",
        "interest rate",
    )
    return any(k in lower for k in non_fin) and not any(k in lower for k in fin)


def generate_dataset(
    cfg: AppCfg, prompt_override: str | None = None, count_override: int | None = None
):
    out_root = Path(cfg.output.local.destination)
    out_root.mkdir(parents=True, exist_ok=True)

    prompt: str = (
        prompt_override
        if prompt_override is not None
        else getattr(cfg.dataset, "prompt", "")
    ) or ""
    count: int = (
        int(count_override) if count_override is not None else int(cfg.dataset.count)
    )

    llm_enabled = (
        cfg.llm.provider == "ollama"
        and cfg.llm.ollama.enabled
        or cfg.llm.provider == "bedrock"
        and cfg.llm.bedrock.enabled
    )

    llm_client = create_llm_client(
        provider=cfg.llm.provider,
        ollama_base_url=cfg.llm.ollama.base_url,
        ollama_model=cfg.llm.ollama.model,
        ollama_timeout=cfg.llm.ollama.timeout_s,
        bedrock_region=cfg.llm.bedrock.region,
        bedrock_model_id=cfg.llm.bedrock.model_id,
        bedrock_temperature=cfg.llm.bedrock.temperature,
    )

    scenario_factory = ScenarioFactory(
        enabled=llm_enabled,
        provider=cfg.llm.provider,
        llm_client=llm_client,
    )

    designer = TemplateDesigner(
        enabled=llm_enabled,
        provider=cfg.llm.provider,
        llm_client=llm_client,
    )

    allowed_letter_templates = list(getattr(cfg.dataset.letter, "templates", []) or [])

    for i in range(count):
        doc_id = f"doc_{i:05d}_{random.randint(1000, 9999)}"
        doc_dir = (
            out_root / doc_id
            if getattr(cfg.dataset, "group_by_document", True)
            else out_root
        )
        doc_dir.mkdir(parents=True, exist_ok=True)

        pages_dir = doc_dir / "pages"
        pages_dir.mkdir(parents=True, exist_ok=True)

        pdf_path = doc_dir / f"{doc_id}.pdf"
        gt_path = doc_dir / f"{doc_id}.json"

        sc = scenario_factory.next(prompt)

        design = designer.next(
            prompt,
            allowed_letter_templates=allowed_letter_templates,
        )

        theme = Theme(
            company_name=sc.company_name,
            accent_rgb=sc.accent_rgb,
            logo_style=sc.logo_style,
            paper_tint_rgb=getattr(sc, "paper_tint_rgb", None),
            header_alignment=getattr(design, "header_alignment", None)
            or getattr(sc, "header_alignment", "left"),
            logo_position=getattr(design, "logo_position", None)
            or getattr(sc, "logo_position", "auto"),
            base_font=getattr(design, "base_font", None)
            or getattr(sc, "base_font", "Helvetica"),
            mono_font=getattr(design, "mono_font", None)
            or getattr(sc, "mono_font", "Courier"),
        )

        if prompt.strip():
            is_stmt = getattr(design, "doc_type", "letter") == "statement"
        else:
            is_stmt = random.random() < cfg.dataset.mix.statement

        if prompt.strip() and _looks_non_financial(prompt):
            is_stmt = False

        if is_stmt:
            stmt = make_statement(
                doc_id,
                theme.company_name,
                cfg.dataset.statement.min_rows,
                cfg.dataset.statement.max_rows,
            )

            render_statement_pdf(
                stmt,
                pdf_path,
                cfg.render.watermark_text,
                theme=theme,
                page_size=cfg.render.page_size,
                rows_per_page=cfg.dataset.statement.rows_per_page,
                pages_max=cfg.dataset.statement.pages_max,
            )

            page_paths = render_statement_pages_jpg(
                stmt,
                out_dir=pages_dir,
                base_name=doc_id,
                watermark=cfg.render.watermark_text,
                theme=theme,
                width=cfg.render.jpg.width,
                height=cfg.render.jpg.height,
                rows_per_page=cfg.dataset.statement.rows_per_page,
                pages_max=cfg.dataset.statement.pages_max,
                font_jitter_prob=getattr(cfg.noise, "font_jitter_prob", 0.0),
                font_jitter_strength=getattr(cfg.noise, "font_jitter_strength", 0.0),
            )

            if cfg.noise.enable:
                for p in page_paths:
                    apply_noise_pipeline(
                        p,
                        rotate_deg_max=cfg.noise.rotate_deg_max,
                        blur_radius_max=cfg.noise.blur_radius_max,
                        contrast_jitter=cfg.noise.contrast_jitter,
                        brightness_jitter=cfg.noise.brightness_jitter,
                        speckle_amount=cfg.noise.speckle_amount,
                        jpeg_recompress=cfg.noise.jpeg_recompress,
                        jpeg_quality_min=cfg.noise.jpeg_quality_min,
                        jpeg_quality_max=cfg.noise.jpeg_quality_max,
                        partial_crop_prob=cfg.noise.partial_crop_prob,
                        crop_margin_max=cfg.noise.crop_margin_max,
                        smudge_prob=cfg.noise.smudge_prob,
                        smudge_strength=cfg.noise.smudge_strength,
                        downsample_prob=cfg.noise.downsample_prob,
                        downsample_min_scale=cfg.noise.downsample_min_scale,
                        downsample_max_scale=cfg.noise.downsample_max_scale,
                        text_damage_prob=cfg.noise.text_damage_prob,
                        text_damage_zones_min=cfg.noise.text_damage_zones_min,
                        text_damage_zones_max=cfg.noise.text_damage_zones_max,
                        text_damage_strength=cfg.noise.text_damage_strength,
                        text_damage_box_min_px=cfg.noise.text_damage_box_min_px,
                        text_damage_box_max_px=cfg.noise.text_damage_box_max_px,
                    )

            vis = _visibility_flags("statement")
            gt = GroundTruth(
                doc_type="statement",
                doc_id=doc_id,
                fields={
                    "industry": GroundTruthField(
                        value=getattr(sc, "industry", "unknown"), visible=True
                    ),
                    "company_name": GroundTruthField(
                        value=theme.company_name, visible=True
                    ),
                    "owner_full_name": GroundTruthField(
                        value=stmt.owner.full_name, visible=True
                    ),
                    "owner_address_lines": GroundTruthField(
                        value=stmt.owner.address_lines,
                        visible=vis["owner_address_lines"],
                    ),
                    "owner_city": GroundTruthField(value=stmt.owner.city, visible=True),
                    "owner_postcode": GroundTruthField(
                        value=stmt.owner.postcode, visible=vis["owner_postcode"]
                    ),
                    "sort_code": GroundTruthField(
                        value=stmt.account.sort_code, visible=vis["sort_code"]
                    ),
                    "account_number": GroundTruthField(
                        value=stmt.account.account_number, visible=vis["account_number"]
                    ),
                    "issue_date": GroundTruthField(
                        value=stmt.issue_date.isoformat(), visible=True
                    ),
                    "period_from": GroundTruthField(
                        value=stmt.period_from.isoformat(), visible=vis["period"]
                    ),
                    "period_to": GroundTruthField(
                        value=stmt.period_to.isoformat(), visible=vis["period"]
                    ),
                    "opening_balance": GroundTruthField(
                        value=stmt.opening_balance, visible=vis["opening_balance"]
                    ),
                    "closing_balance": GroundTruthField(
                        value=stmt.closing_balance, visible=vis["closing_balance"]
                    ),
                    "transactions": GroundTruthField(
                        value=[t.model_dump() for t in stmt.transactions], visible=True
                    ),
                },
                meta={
                    "prompt": prompt,
                    "watermark": cfg.render.watermark_text,
                    "pdf": pdf_path.name,
                    "jpg_pages": [p.name for p in page_paths],
                    "theme": {
                        "accent_rgb": theme.accent_rgb,
                        "logo_style": theme.logo_style,
                        "paper_tint_rgb": theme.paper_tint_rgb,
                        "header_alignment": theme.header_alignment,
                        "logo_position": theme.logo_position,
                        "base_font": theme.base_font,
                        "mono_font": theme.mono_font,
                    },
                },
            )
            gt_path.write_text(gt.model_dump_json(indent=2), encoding="utf-8")

        else:
            template = getattr(design, "letter_template", None) or (
                random.choice(allowed_letter_templates)
                if allowed_letter_templates
                else "service_change_notice"
            )

            letter = make_letter(doc_id, theme.company_name, template)

            render_letter_pdf(
                letter,
                pdf_path,
                cfg.render.watermark_text,
                theme=theme,
                page_size=cfg.render.page_size,
            )

            jpg_path = pages_dir / f"{doc_id}.jpg"
            render_letter_jpg(
                letter,
                jpg_path,
                cfg.render.watermark_text,
                theme=theme,
                width=cfg.render.jpg.width,
                height=cfg.render.jpg.height,
                font_jitter_prob=getattr(cfg.noise, "font_jitter_prob", 0.0),
                font_jitter_strength=getattr(cfg.noise, "font_jitter_strength", 0.0),
            )

            if cfg.noise.enable:
                apply_noise_pipeline(
                    jpg_path,
                    rotate_deg_max=cfg.noise.rotate_deg_max,
                    blur_radius_max=cfg.noise.blur_radius_max,
                    contrast_jitter=cfg.noise.contrast_jitter,
                    brightness_jitter=cfg.noise.brightness_jitter,
                    speckle_amount=cfg.noise.speckle_amount,
                    jpeg_recompress=cfg.noise.jpeg_recompress,
                    jpeg_quality_min=cfg.noise.jpeg_quality_min,
                    jpeg_quality_max=cfg.noise.jpeg_quality_max,
                    partial_crop_prob=cfg.noise.partial_crop_prob,
                    crop_margin_max=cfg.noise.crop_margin_max,
                    smudge_prob=cfg.noise.smudge_prob,
                    smudge_strength=cfg.noise.smudge_strength,
                    downsample_prob=cfg.noise.downsample_prob,
                    downsample_min_scale=cfg.noise.downsample_min_scale,
                    downsample_max_scale=cfg.noise.downsample_max_scale,
                    text_damage_prob=cfg.noise.text_damage_prob,
                    text_damage_zones_min=cfg.noise.text_damage_zones_min,
                    text_damage_zones_max=cfg.noise.text_damage_zones_max,
                    text_damage_strength=cfg.noise.text_damage_strength,
                    text_damage_box_min_px=cfg.noise.text_damage_box_min_px,
                    text_damage_box_max_px=cfg.noise.text_damage_box_max_px,
                )

            vis = _visibility_flags("letter")
            gt = GroundTruth(
                doc_type="letter",
                doc_id=doc_id,
                fields={
                    "industry": GroundTruthField(
                        value=getattr(sc, "industry", "unknown"), visible=True
                    ),
                    "company_name": GroundTruthField(
                        value=theme.company_name, visible=True
                    ),
                    "template": GroundTruthField(value=template, visible=True),
                    "subject": GroundTruthField(value=letter.subject, visible=True),
                    "owner_full_name": GroundTruthField(
                        value=letter.owner.full_name, visible=True
                    ),
                    "owner_address_lines": GroundTruthField(
                        value=letter.owner.address_lines,
                        visible=vis["owner_address_lines"],
                    ),
                    "owner_city": GroundTruthField(
                        value=letter.owner.city, visible=True
                    ),
                    "owner_postcode": GroundTruthField(
                        value=letter.owner.postcode, visible=vis["owner_postcode"]
                    ),
                    "sort_code": GroundTruthField(
                        value=letter.account.sort_code, visible=vis["sort_code"]
                    ),
                    "account_number": GroundTruthField(
                        value=letter.account.account_number,
                        visible=vis["account_number"],
                    ),
                    "issue_date": GroundTruthField(
                        value=letter.issue_date.isoformat(), visible=True
                    ),
                    "body_paragraphs": GroundTruthField(
                        value=letter.body_paragraphs, visible=True
                    ),
                    "table_headers": GroundTruthField(
                        value=letter.table_headers, visible=bool(letter.table_headers)
                    ),
                    "table_rows": GroundTruthField(
                        value=letter.table_rows, visible=bool(letter.table_rows)
                    ),
                },
                meta={
                    "prompt": prompt,
                    "watermark": cfg.render.watermark_text,
                    "pdf": pdf_path.name,
                    "jpg": jpg_path.name,
                    "theme": {
                        "accent_rgb": theme.accent_rgb,
                        "logo_style": theme.logo_style,
                        "paper_tint_rgb": theme.paper_tint_rgb,
                        "header_alignment": theme.header_alignment,
                        "logo_position": theme.logo_position,
                        "base_font": theme.base_font,
                        "mono_font": theme.mono_font,
                    },
                },
            )
            gt_path.write_text(gt.model_dump_json(indent=2), encoding="utf-8")

    print(f"Done. Wrote to: {out_root.resolve()}")
