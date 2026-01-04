from __future__ import annotations
def _draw_polygon(c, points, stroke=1, fill=0):
    """ReportLab Canvas doesn't expose polygon() on all builds; draw via a path."""
    if not points:
        return
    p = c.beginPath()
    x0, y0 = points[0]
    p.moveTo(x0, y0)
    for x, y in points[1:]:
        p.lineTo(x, y)
    p.close()
    c.drawPath(p, stroke=stroke, fill=fill)




from dataclasses import dataclass
from reportlab.lib import colors
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import mm
from PIL import ImageDraw, ImageFont
import random

@dataclass
class Theme:
    company_name: str
    accent_rgb: tuple[int,int,int]
    logo_style: str
    paper_tint_rgb: tuple[int,int,int] | None
    header_alignment: str
    logo_position: str = "auto"  # auto|left|center|right
    base_font: str = "Helvetica"
    mono_font: str = "Courier"  # monospace

def _bold_font(base: str) -> str:
    base = (base or "Helvetica").strip()
    # ReportLab "built-in 14 fonts" naming quirks:
    if base == "Times-Roman":
        return "Times-Bold"
    if base == "Helvetica":
        return "Helvetica-Bold"
    if base == "Courier":
        return "Courier-Bold"

    # Fallbacks: if you later register TTF fonts, "<name>-Bold" might exist
    return f"{base}-Bold"


def _font(size: int):
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except Exception:
        return ImageFont.load_default()

def _pick_logo_position(theme, header_alignment: str):
    pos = (getattr(theme, "logo_position", None) or "auto").lower().strip()
    if pos == "auto":
        # default: align with header alignment
        pos = (header_alignment or "left").lower().strip()
    if pos not in ("left","center","right"):
        pos = "left"
    return pos


def pdf_draw_header(c: Canvas, theme: Theme, title: str, x_mm: float, y_mm: float, page_w):
    r,g,b = theme.accent_rgb
    c.saveState()
    c.setFillColor(colors.Color(r/255, g/255, b/255))
    c.setFont(_bold_font(getattr(theme, "base_font", "Helvetica")), 16)

    x = x_mm*mm
    if theme.header_alignment == "center":
        c.drawCentredString(page_w/2, y_mm*mm, theme.company_name)
        c.setFont(_bold_font(getattr(theme, "base_font", "Helvetica")), 16)
        c.drawCentredString(page_w/2, (y_mm-6)*mm, title)
        lx = page_w/2 - 60
    elif theme.header_alignment == "right":
        c.drawRightString(page_w-20*mm, y_mm*mm, theme.company_name)
        c.setFont(_bold_font(getattr(theme, "base_font", "Helvetica")), 16)
        c.drawRightString(page_w-20*mm, (y_mm-6)*mm, title)
        lx = page_w - 140
    else:
        c.drawString(x, y_mm*mm, theme.company_name)
        c.setFont(_bold_font(getattr(theme, "base_font", "Helvetica")), 16)
        c.drawString(x, (y_mm-6)*mm, title)
        lx = x - 10*mm

    ly = (y_mm+2)*mm
    c.setStrokeColor(colors.Color(r/255, g/255, b/255))
    c.setFillColor(colors.Color(r/255, g/255, b/255))

    if theme.logo_style == "nb_bars":
        for i in range(3):
            c.rect(lx + i*10, ly, 6, 24, fill=1, stroke=0)
    elif theme.logo_style == "c_circle":
        c.circle(lx+16, ly+12, 12, fill=0, stroke=1)
        c.circle(lx+16, ly+12, 6, fill=1, stroke=0)
    elif theme.logo_style == "h_wave":
        c.setLineWidth(2)
        c.bezier(lx, ly+6, lx+18, ly+28, lx+36, ly-4, lx+54, ly+16)
    elif theme.logo_style == "a_triangle":
        _draw_polygon(c, [(lx+16, ly+26), (lx+2, ly+2), (lx+30, ly+2)], stroke=1, fill=0)
    else:
        c.setLineWidth(4)
        c.line(lx+2, ly+24, lx+34, ly+2)

    c.restoreState()

def jpg_draw_header(d: ImageDraw.ImageDraw, theme: Theme, title: str, x: int, y: int, page_w: int):
    r,g,b = theme.accent_rgb
    name_font = _font(44)
    sub_font = _font(20)

    if theme.header_alignment == "center":
        tw = d.textlength(theme.company_name, font=name_font)
        d.text(((page_w-tw)//2, y), theme.company_name, font=name_font, fill=(r,g,b))
        stw = d.textlength(title, font=sub_font)
        d.text(((page_w-stw)//2, y+54), title, font=sub_font, fill=(0,0,0))
        lx = (page_w//2) - 70
    elif theme.header_alignment == "right":
        tw = d.textlength(theme.company_name, font=name_font)
        d.text((page_w - tw - 80, y), theme.company_name, font=name_font, fill=(r,g,b))
        stw = d.textlength(title, font=sub_font)
        d.text((page_w - stw - 80, y+54), title, font=sub_font, fill=(0,0,0))
        lx = page_w - 240
    else:
        d.text((x, y), theme.company_name, font=name_font, fill=(r,g,b))
        d.text((x, y+54), title, font=sub_font, fill=(0,0,0))
        lx = x-60

    ly = y+8
    if theme.logo_style == "nb_bars":
        for i in range(3):
            d.rectangle([lx+i*16, ly, lx+i*16+10, ly+40], fill=(r,g,b))
    elif theme.logo_style == "c_circle":
        d.ellipse([lx, ly, lx+46, ly+46], outline=(r,g,b), width=4)
        d.ellipse([lx+17, ly+17, lx+29, ly+29], fill=(r,g,b))
    elif theme.logo_style == "h_wave":
        d.line([lx, ly+24, lx+18, ly+6, lx+36, ly+38, lx+54, ly+20], fill=(r,g,b), width=4)
    elif theme.logo_style == "a_triangle":
        d.polygon([ (lx+22, ly+44), (lx+2, ly+4), (lx+42, ly+4) ], outline=(r,g,b))
    else:
        d.line([lx+4, ly+44, lx+44, ly+4], fill=(r,g,b), width=5)

# Backwards-compatible alias (older versions used this name)
def pdf_brand_header(c, theme: Theme, title: str, x_mm: float, y_mm: float, page_w=None):
    return pdf_draw_header(c, theme, title, x_mm, y_mm, page_w=page_w)
