from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from .models import StatementDoc, LetterDoc
from .branding import Theme, jpg_draw_header
import random

def _font(name: str, size: int):
    try:
        return ImageFont.truetype(name, size)
    except Exception:
        return ImageFont.load_default()

SANS = "DejaVuSans.ttf"
MONO = "DejaVuSansMono.ttf"

def _wrap(text: str, width: int):
    words = text.split()
    lines, cur, n = [], [], 0
    for w in words:
        if n + len(w) + (1 if cur else 0) > width:
            lines.append(" ".join(cur)); cur=[w]; n=len(w)
        else:
            cur.append(w); n += len(w) + (1 if len(cur)>1 else 0)
    if cur: lines.append(" ".join(cur))
    return lines

def _paper_bg(width: int, height: int, tint):
    if not tint:
        return Image.new("RGB", (width, height), "white")
    r,g,b = tint
    base = Image.new("RGB", (width, height), (255,255,255))
    overlay = Image.new("RGB", (width, height), (r,g,b))
    return Image.blend(base, overlay, alpha=0.08)

def _draw_text_jittered(d: ImageDraw.ImageDraw, xy, text: str, font_size: int, fill, strength: float):
    x, y = xy
    f_sans = _font(SANS, font_size)
    f_mono = _font(MONO, font_size)
    for ch in text:
        use_mono = ch.isdigit() and (random.random() < 0.65)
        f = f_mono if use_mono else f_sans
        dx = int(random.uniform(-1, 1) * 3 * strength) if ch.isdigit() else 0
        dy = int(random.uniform(-1, 1) * 2 * strength) if ch.isdigit() else 0
        d.text((x+dx, y+dy), ch, font=f, fill=fill)
        x += int(d.textlength(ch, font=f))

def render_statement_pages_jpg(stmt: StatementDoc, out_dir: Path, base_name: str, watermark: str,
                               theme: Theme, width: int, height: int, rows_per_page: int = 40, pages_max: int = 4,
                               font_jitter_prob: float = 0.0, font_jitter_strength: float = 0.35) -> list[Path]:
    rows_per_page = max(10, rows_per_page)
    pages = [stmt.transactions[i:i+rows_per_page] for i in range(0, len(stmt.transactions), rows_per_page)]
    pages = pages[:max(1, pages_max)]

    out_paths: list[Path] = []
    for pi, txns in enumerate(pages, start=1):
        img = _paper_bg(width, height, theme.paper_tint_rgb)
        d = ImageDraw.Draw(img)

        d.text((60, 60), watermark, font=_font(SANS, 26), fill=(210,210,210))

        y = 120
        jpg_draw_header(d, theme, f"Statement (page {pi}/{len(pages)})", 120, y, page_w=width)
        y += 90

        f = _font(SANS, 18)
        f_small = _font(SANS, 16)
        d.text((80, y), f"Issue date: {stmt.issue_date.strftime('%d %b %Y')}", font=f, fill="black"); y += 28
        d.text((80, y), f"Period: {stmt.period_from.strftime('%d %b %Y')} to {stmt.period_to.strftime('%d %b %Y')}", font=f, fill="black"); y += 45

        if pi == 1:
            d.text((80, y), stmt.owner.full_name, font=_font(SANS, 22), fill="black"); y += 30
            for line in stmt.owner.address_lines[:3]:
                d.text((80, y), line[:80], font=f, fill="black"); y += 26
            d.text((80, y), f"{stmt.owner.city}  {stmt.owner.postcode}", font=f, fill="black"); y += 40
            d.text((80, y), f"Sort code: {stmt.account.sort_code}    Account: {stmt.account.account_number}", font=f, fill="black"); y += 45
            d.text((80, y), f"Opening balance: £{stmt.opening_balance:,.2f}", font=f, fill="black"); y += 26
            d.text((80, y), f"Closing balance: £{stmt.closing_balance:,.2f}", font=f, fill="black"); y += 40
        else:
            d.text((80, y), f"Sort code: {stmt.account.sort_code}    Account: {stmt.account.account_number}", font=f, fill="black"); y += 50

        d.text((80, y), "Date", font=f_small, fill="black")
        d.text((240, y), "Description", font=f_small, fill="black")
        d.text((1100, y), "Paid in", font=f_small, fill="black")
        d.text((1250, y), "Paid out", font=f_small, fill="black")
        d.text((1420, y), "Balance", font=f_small, fill="black")
        y += 22
        d.line((80, y, width-80, y), fill=(120,120,120), width=2)
        y += 18

        jitter = (random.random() < font_jitter_prob)
        for t in txns:
            d.text((80, y), t.txn_date.strftime('%d %b %Y'), font=f_small, fill="black")
            d.text((240, y), t.description[:55], font=f_small, fill="black")
            pin = f"£{t.paid_in:,.2f}" if t.paid_in else ""
            pout = f"£{t.paid_out:,.2f}" if t.paid_out else ""
            bal = f"£{t.running_balance:,.2f}"

            if jitter:
                _draw_text_jittered(d, (1100, y), pin, 16, "black", font_jitter_strength)
                _draw_text_jittered(d, (1250, y), pout, 16, "black", font_jitter_strength)
                _draw_text_jittered(d, (1420, y), bal, 16, "black", font_jitter_strength)
            else:
                d.text((1100, y), pin, font=f_small, fill="black")
                d.text((1250, y), pout, font=f_small, fill="black")
                d.text((1420, y), bal, font=f_small, fill="black")

            y += 24
            if y > height - 260:
                break

        if pi == len(pages):
            y += 20
            d.text((80, y), "Notes:", font=f_small, fill="black"); y += 26
            for n in stmt.footer_notes[:6]:
                d.text((95, y), f"• {n}"[:110], font=f_small, fill="black"); y += 22

        out_path = out_dir / f"{base_name}_p{pi}.jpg"
        img.save(out_path, quality=92)
        out_paths.append(out_path)

    return out_paths

def render_letter_jpg(letter: LetterDoc, out_path: Path, watermark: str, theme: Theme, width: int, height: int,
                      font_jitter_prob: float = 0.0, font_jitter_strength: float = 0.35):
    img = _paper_bg(width, height, theme.paper_tint_rgb)
    d = ImageDraw.Draw(img)
    d.text((60, 60), watermark, font=_font(SANS, 26), fill=(210,210,210))

    y = 120
    jpg_draw_header(d, theme, "Letter", 120, y, page_w=width)
    y += 90

    f_h = _font(SANS, 22)
    f = _font(SANS, 18)
    f_small = _font(SANS, 16)

    d.text((80, y), f"Date: {letter.issue_date.strftime('%d %b %Y')}", font=f, fill="black"); y += 50
    d.text((80, y), letter.owner.full_name, font=f_h, fill="black"); y += 30
    for line in letter.owner.address_lines[:3]:
        d.text((80, y), line[:80], font=f, fill="black"); y += 26
    d.text((80, y), f"{letter.owner.city}  {letter.owner.postcode}", font=f, fill="black"); y += 50

    d.text((80, y), f"Subject: {letter.subject}"[:110], font=f_h, fill="black"); y += 40

    sc = letter.display_sort_code or letter.account.sort_code
    an = letter.display_account_number or letter.account.account_number

    jitter = (random.random() < font_jitter_prob)
    if jitter:
        _draw_text_jittered(d, (80, y), f"Sort code: {sc}", 18, "black", font_jitter_strength); y += 26
        _draw_text_jittered(d, (80, y), f"Account no: {an}", 18, "black", font_jitter_strength); y += 50
    else:
        d.text((80, y), f"Sort code: {sc}", font=f, fill="black"); y += 26
        d.text((80, y), f"Account no: {an}", font=f, fill="black"); y += 50

    for para in letter.body_paragraphs[:7]:
        for line in _wrap(para, 92):
            d.text((80, y), line, font=f, fill="black"); y += 24
            if y > height - 420:
                break
        y += 16
        if y > height - 420:
            break

    if letter.table_headers and letter.table_rows and y < height - 360:
        d.text((80, y), (letter.table_title or "Details")[:60], font=f_h, fill="black"); y += 34
        cols = len(letter.table_headers)
        col_w = (width - 160) // max(1, cols)
        d.rectangle([80, y, width-80, y+28], outline=(160,160,160), fill=(245,245,245))
        for i,hdr in enumerate(letter.table_headers):
            d.text((85 + i*col_w, y+6), str(hdr)[:18], font=f_small, fill="black")
        y += 28
        for r in letter.table_rows[:10]:
            d.rectangle([80, y, width-80, y+26], outline=(210,210,210))
            for i,cell in enumerate(r[:cols]):
                d.text((85 + i*col_w, y+5), str(cell)[:22], font=f_small, fill="black")
            y += 26
            if y > height - 260:
                break
        y += 18

    if letter.optional_lines and y < height - 240:
        d.text((80, y), "Additional information", font=f_h, fill="black"); y += 34
        for l in letter.optional_lines[:10]:
            d.text((95, y), f"• {l}"[:110], font=f_small, fill="black"); y += 22
            if y > height - 220:
                break

    y += 24
    d.text((80, y), "Yours sincerely,", font=f, fill="black"); y += 70
    d.text((80, y), "Customer Support (Synthetic)", font=f_h, fill="black")

    img.save(out_path, quality=92)
