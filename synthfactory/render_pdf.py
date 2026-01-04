from __future__ import annotations
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
from pathlib import Path
from .models import StatementDoc, LetterDoc
from .branding import Theme, pdf_draw_header
import random

def _page_size(name: str):
    return A4

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

def _watermark(c: canvas.Canvas, w: float, h: float, watermark: str):
    c.saveState()
    c.setFillColor(colors.lightgrey)
    c.setFont("Helvetica-Bold", 26)
    c.translate(w/2, h/2)
    c.rotate(25)
    c.drawCentredString(0, 0, watermark)
    c.restoreState()

def _tinted_background(c: canvas.Canvas, w: float, h: float, tint_rgb):
    if not tint_rgb: return
    r,g,b = tint_rgb
    c.saveState()
    c.setFillColor(colors.Color(r/255, g/255, b/255, alpha=0.10))
    c.rect(0,0,w,h, stroke=0, fill=1)
    c.restoreState()

def render_statement_pdf(stmt: StatementDoc, out_path: Path, watermark: str, theme: Theme,
                         page_size: str = "A4", rows_per_page: int = 40, pages_max: int = 4):
    w, h = _page_size(page_size)
    c = canvas.Canvas(str(out_path), pagesize=(w, h))

    rows_per_page = max(10, rows_per_page)
    pages = [stmt.transactions[i:i+rows_per_page] for i in range(0, len(stmt.transactions), rows_per_page)]
    pages = pages[:max(1, pages_max)]

    for page_idx, txns in enumerate(pages, start=1):
        _tinted_background(c, w, h, theme.paper_tint_rgb)
        _watermark(c, w, h, watermark)

        y = h - 20*mm
        pdf_draw_header(c, theme, f"Statement (page {page_idx}/{len(pages)})", 28, y/mm, page_w=w)
        y -= 18*mm

        c.setFillColor(colors.black)
        c.setFont("Helvetica", 10)
        c.drawString(20*mm, y, f"Issue date: {stmt.issue_date.strftime('%d %b %Y')}"); y -= 5*mm
        c.drawString(20*mm, y, f"Period: {stmt.period_from.strftime('%d %b %Y')} to {stmt.period_to.strftime('%d %b %Y')}"); y -= 8*mm

        if page_idx == 1:
            c.setFont("Helvetica-Bold", 10)
            c.drawString(20*mm, y, stmt.owner.full_name); y -= 4.5*mm
            c.setFont("Helvetica", 10)
            for line in stmt.owner.address_lines[:3]:
                c.drawString(20*mm, y, line[:80]); y -= 4.5*mm
            c.drawString(20*mm, y, f"{stmt.owner.city}  {stmt.owner.postcode}"); y -= 7*mm

            c.setFont("Helvetica-Bold", 10); c.drawString(20*mm, y, "Account"); y -= 4.5*mm
            c.setFont("Helvetica", 10)
            c.drawString(20*mm, y, f"Sort code: {stmt.account.sort_code}    Account: {stmt.account.account_number}"); y -= 7*mm

            c.setFont("Helvetica-Bold", 10)
            c.drawString(20*mm, y, f"Opening balance: £{stmt.opening_balance:,.2f}"); y -= 4.5*mm
            c.drawString(20*mm, y, f"Closing balance: £{stmt.closing_balance:,.2f}"); y -= 8*mm
        else:
            c.drawString(20*mm, y, f"Sort code: {stmt.account.sort_code}    Account: {stmt.account.account_number}"); y -= 10*mm

        c.setFont("Helvetica-Bold", 9)
        c.drawString(20*mm, y, "Date"); c.drawString(40*mm, y, "Description")
        c.drawRightString(150*mm, y, "Paid in"); c.drawRightString(175*mm, y, "Paid out"); c.drawRightString(200*mm, y, "Balance")
        y -= 4*mm
        c.setStrokeColor(colors.grey); c.line(20*mm, y, 200*mm, y); y -= 4*mm

        c.setFont("Helvetica", 8.5)
        for t in txns:
            c.drawString(20*mm, y, t.txn_date.strftime('%d %b %Y'))
            c.drawString(40*mm, y, t.description[:55])
            c.drawRightString(150*mm, y, f"£{t.paid_in:,.2f}" if t.paid_in else "")
            c.drawRightString(175*mm, y, f"£{t.paid_out:,.2f}" if t.paid_out else "")
            c.drawRightString(200*mm, y, f"£{t.running_balance:,.2f}")
            y -= 4.2*mm

        if page_idx == len(pages):
            y -= 6*mm
            c.setFont("Helvetica-Bold", 9); c.drawString(20*mm, y, "Notes"); y -= 4.5*mm
            c.setFont("Helvetica", 8.5)
            for n in stmt.footer_notes[:8]:
                c.drawString(22*mm, y, f"• {n}"[:110]); y -= 4.2*mm

        c.showPage()

    c.save()

def _draw_simple_table_pdf(c, x, y, table_width, title, headers, rows, font_name="Helvetica", font_size=9, row_height=6*mm, max_rows=14):
    from reportlab.lib import colors
    c.setFillColor(colors.black)
    if title:
        c.setFont(font_name, 10)
        c.drawString(x, y, str(title)[:110]); y -= row_height

    cols = len(headers) if headers else 0
    if cols <= 0:
        return y
    col_w = table_width / cols

    c.setFillColor(colors.whitesmoke)
    c.rect(x, y-row_height+2, table_width, row_height, stroke=0, fill=1)
    c.setFillColor(colors.black)
    bold = "Helvetica-Bold" if font_name == "Helvetica" else font_name
    c.setFont(bold, font_size)
    for i, h in enumerate(headers):
        c.drawString(x + i*col_w + 4, y - row_height + 6, str(h)[:28])
    y -= row_height

    c.setFont(font_name, font_size)
    shown = (rows or [])[:max_rows]
    for r in shown:
        c.setStrokeColor(colors.lightgrey)
        c.line(x, y, x+table_width, y)
        for i in range(cols+1):
            c.line(x+i*col_w, y, x+i*col_w, y-row_height)
        c.setStrokeColor(colors.black)
        for i, cell in enumerate(r[:cols]):
            c.drawString(x + i*col_w + 4, y - row_height + 6, str(cell)[:32])
        y -= row_height

    c.setStrokeColor(colors.lightgrey)
    c.line(x, y, x+table_width, y)
    c.setStrokeColor(colors.black)
    return y

def render_letter_pdf(letter: LetterDoc, out_path: Path, watermark: str, theme: Theme, page_size: str = "A4"):
    w, h = _page_size(page_size)
    c = canvas.Canvas(str(out_path), pagesize=(w, h))
    _tinted_background(c, w, h, theme.paper_tint_rgb)
    _watermark(c, w, h, watermark)

    y = h - 20*mm
    pdf_draw_header(c, theme, "Letter", 28, y/mm, page_w=w)
    y -= 18*mm

    c.setFillColor(colors.black)
    c.setFont("Helvetica", 10)
    c.drawString(20*mm, y, f"Date: {letter.issue_date.strftime('%d %b %Y')}"); y -= 10*mm

    c.setFont("Helvetica-Bold", 10)
    c.drawString(20*mm, y, letter.owner.full_name); y -= 4.5*mm
    c.setFont("Helvetica", 10)
    for line in letter.owner.address_lines[:3]:
        c.drawString(20*mm, y, line[:80]); y -= 4.5*mm
    c.drawString(20*mm, y, f"{letter.owner.city}  {letter.owner.postcode}"); y -= 10*mm

    c.setFont("Helvetica-Bold", 11)
    c.drawString(20*mm, y, f"Subject: {letter.subject}"[:110]); y -= 7*mm

    sc = letter.display_sort_code or letter.account.sort_code
    an = letter.display_account_number or letter.account.account_number

    c.setFont("Helvetica", 10)
    c.drawString(20*mm, y, f"Sort code: {sc}"); y -= 5*mm
    c.setFont(random.choice(["Helvetica", "Courier"]), 10)
    c.drawString(20*mm, y, f"Account no: {an}"); y -= 15*mm
    c.setFont("Helvetica", 10)

    for para in letter.body_paragraphs:
        for line in _wrap(para, 95):
            c.drawString(20*mm, y, line); y -= 4.5*mm
            if y < 30*mm:
                break
        y -= 4.5*mm
        if y < 30*mm:
            break

    if letter.table_rows and letter.table_headers and y > 55*mm:
        y -= 3*mm
        y = _draw_simple_table_pdf(
            c, x=20*mm, y=y, table_width=w - 40*mm,
            title=letter.table_title, headers=letter.table_headers, rows=letter.table_rows,
            font_name="Helvetica", font_size=9, row_height=6*mm, max_rows=14
        )
        y -= 6*mm

    if letter.optional_lines and y > 40*mm:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(20*mm, y, "Additional information"); y -= 5.5*mm
        c.setFont("Helvetica", 9.5)
        for l in letter.optional_lines[:10]:
            c.drawString(22*mm, y, f"• {l}"[:110]); y -= 4.5*mm
            if y < 25*mm:
                break

    y -= 8*mm
    c.setFont("Helvetica", 10); c.drawString(20*mm, y, "Yours sincerely,"); y -= 15*mm
    c.setFont("Helvetica-Bold", 10); c.drawString(20*mm, y, "Customer Support (Synthetic)")
    c.save()
