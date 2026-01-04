from __future__ import annotations

import random
from datetime import date, timedelta
from faker import Faker

from .models import Person, Account, Transaction, StatementDoc, LetterDoc

fake = Faker("en_GB")

def _sort_code() -> str:
    return f"{random.randint(10,99)}-{random.randint(10,99)}-{random.randint(10,99)}"

def _acc_no() -> str:
    return str(random.randint(20000000, 99999999))

def _money(min_v: float = 5.0, max_v: float = 1500.0) -> str:
    v = round(random.uniform(min_v, max_v), 2)
    return f"£{v:,.2f}"

def _maybe(v, p=0.5):
    return v if random.random() < p else None

def _date_str(d: date) -> str:
    return d.strftime("%d %b %Y")

def _rand_future(days_min=1, days_max=45) -> date:
    return date.today() + timedelta(days=random.randint(days_min, days_max))

def _rand_past(days_min=0, days_max=45) -> date:
    return date.today() - timedelta(days=random.randint(days_min, days_max))

def _rand_ref(prefix="REF") -> str:
    return f"{prefix}-{random.randint(100000, 999999)}"

def _pick(items):
    return random.choice(list(items))

def _phone() -> str:
    return f"+44 {random.randint(7000, 7999)} {random.randint(100000, 999999)}"


def make_person() -> Person:
    lines = [fake.street_address()]
    if random.random() < 0.25:
        lines.append(fake.secondary_address())
    return Person(
        full_name=fake.name(),
        address_lines=lines,
        city=fake.city(),
        postcode=fake.postcode()
    )

def make_account(bank_name: str) -> Account:
    return Account(sort_code=_sort_code(), account_number=_acc_no(), bank_name=bank_name)


def make_statement(doc_id: str, bank_name: str, min_rows: int, max_rows: int) -> StatementDoc:
    owner = make_person()
    acc = make_account(bank_name)

    today = date.today()
    period_to = today - timedelta(days=random.randint(0, 5))
    period_from = period_to - timedelta(days=random.randint(25, 40))
    issue_date = period_to + timedelta(days=random.randint(1, 4))

    n = random.randint(min_rows, max_rows)
    bal = round(random.uniform(300, 3500), 2)
    opening = bal

    txns: list[Transaction] = []
    for _ in range(n):
        d = period_from + timedelta(days=random.randint(0, (period_to - period_from).days))
        desc = random.choice([
            fake.company(), "RENT PAYMENT", "MORTGAGE", "INSURANCE", "SALARY",
            "UTILITY BILL", "SUBSCRIPTION", "CARD PAYMENT", "ONLINE TRANSFER", "DIRECT DEBIT",
        ])
        amount = round(random.uniform(4, 1400), 2)
        if random.random() < 0.55:
            paid_out = amount
            paid_in = None
            bal = round(bal - amount, 2)
        else:
            paid_in = amount
            paid_out = None
            bal = round(bal + amount, 2)

        txns.append(Transaction(txn_date=d, description=desc, paid_in=paid_in, paid_out=paid_out, running_balance=bal))

    txns.sort(key=lambda t: (t.txn_date, t.description))
    closing = txns[-1].running_balance if txns else opening

    notes = ["This is a synthetic document generated for testing purposes."]
    if random.random() < 0.3:
        notes.append("Interest was applied in accordance with your agreement.")

    return StatementDoc(doc_id=doc_id, owner=owner, account=acc, issue_date=issue_date,
                        period_from=period_from, period_to=period_to, opening_balance=opening,
                        closing_balance=closing, transactions=txns, footer_notes=notes)


def make_letter(doc_id: str, company_name: str, template: str) -> LetterDoc:
    owner = make_person()
    acc = make_account(company_name)
    issue_date = _rand_past(0, 25)

    subject, paras, opt, table_data = template_content(template, owner_name=owner.full_name)

    display_sc = acc.sort_code if random.random() < 0.75 else acc.sort_code.replace("-", " ")
    display_an = acc.account_number if random.random() < 0.75 else acc.account_number[:4] + " " + acc.account_number[4:]

    table = table_data or {"title": None, "headers": None, "rows": None}

    return LetterDoc(doc_id=doc_id, template=template, owner=owner, account=acc, issue_date=issue_date,
                     subject=subject, body_paragraphs=paras, optional_lines=opt,
                     table_title=table.get("title"), table_headers=table.get("headers"), table_rows=table.get("rows"),
                     display_sort_code=display_sc, display_account_number=display_an)


def template_content(template: str, owner_name: str = "Customer"):
    table = {"title": None, "headers": None, "rows": None}

    templates = {
        "fee_summary": (
            "Summary of fees and charges",
            ["This notice provides a summary of recent fees and charges.", "Please review the items below."],
            ["All values are synthetic and for testing only."],
            {"title": "Fees", "headers": ["Date", "Description", "Amount"],
             "rows": [[_date_str(_rand_past(2, 25)), "Monthly account fee", _money(3, 12)],
                      [_date_str(_rand_past(2, 25)), "Unpaid item fee", _money(8, 18)]]}
        ),
        "payment_schedule": (
            "Payment schedule",
            ["Below is the current payment schedule.", "Payments are shown for information only."],
            ["Contact us if your circumstances change."],
            {"title": "Schedule", "headers": ["Due date", "Reference", "Amount"],
             "rows": [[_date_str(_rand_future(3, 14)), "Instalment 1", _money(50, 250)],
                      [_date_str(_rand_future(34, 45)), "Instalment 2", _money(50, 250)]]}
        ),
        "direct_debit_mandate": (
            "Direct Debit mandate confirmation",
            ["We are writing to confirm the setup of a Direct Debit instruction.", "The instruction will be collected on the agreed date."],
            ["You can cancel a Direct Debit at any time through your bank."],
            None
        ),
        "service_change_notice": (
            "Service change notice",
            [f"We are writing to inform you of an upcoming service change effective {_date_str(_rand_future(3, 35))}."],
            ["This notice is synthetic and for testing only."],
            None
        ),
        "appointment_notice": (
            "Appointment reminder",
            ["This is a reminder of your upcoming appointment.", f"Clinic: {fake.city()} Medical Centre"],
            ["Please arrive 10 minutes early."],
            {"title": "Appointment details", "headers": ["Field", "Value"],
             "rows": [["Patient", owner_name], ["Date", _date_str(_rand_future(1, 20))],
                      ["Clinician", f"Dr {fake.last_name()}"]]}
        ),
        "appointment_payment_notice": (
            "Appointment and payment information",
            ["This letter confirms your appointment and provides billing information."],
            ["All details are synthetic and for testing only."],
            {"title": "Billing summary", "headers": ["Item", "Value"],
             "rows": [["Reference", _rand_ref("CLIN")], ["Amount due", _money(10, 120)]]}
        ),
        "prescription_refill_notice": (
            "Prescription refill reminder",
            ["This notice is a reminder regarding prescription refills."],
            ["Do not stop medication without medical advice."],
            {"title": "Prescription summary", "headers": ["Medication", "Qty"],
             "rows": [[fake.word().capitalize(), str(random.randint(14, 56))],
                      [fake.word().capitalize(), str(random.randint(14, 56))]]}
        ),
        "shipping_schedule": (
            "Shipping schedule notification",
            ["This document provides a schedule of upcoming dispatch routes."],
            ["All routes and identifiers are synthetic."],
            {"title": "Dispatch schedule", "headers": ["Route", "Reference"],
             "rows": [[f"{fake.city()} to {fake.city()}", _rand_ref("SHIP")],
                      [f"{fake.city()} to {fake.city()}", _rand_ref("SHIP")]]}
        ),
        "shipping_manifest": (
            "Shipment manifest",
            ["This manifest lists items included in a shipment."],
            ["For testing only - synthetic manifest data."],
            {"title": "Shipment manifest", "headers": ["Item", "Qty"],
             "rows": [[fake.word().capitalize(), str(random.randint(1, 24))],
                      [fake.word().capitalize(), str(random.randint(1, 24))]]}
        ),
        "delivery_dispute_letter": (
            "Delivery dispute update",
            ["We are writing with an update regarding your delivery dispute."],
            ["This document is synthetic and contains fictional data."],
            {"title": "Dispute details", "headers": ["Field", "Value"],
             "rows": [["Reference", _rand_ref("CASE")], ["Issue", _pick(["Damaged", "Missing", "Late"])]]}
        ),
        "maintenance_notice": (
            "Planned maintenance notification",
            ["We are writing to notify you of planned maintenance."],
            ["Synthetic notice for testing only."],
            {"title": "Maintenance window", "headers": ["Service", "Impact"],
             "rows": [[fake.word().capitalize() + " API", _pick(["Intermittent", "Partial"])]]}
        ),
        "service_outage_notice": (
            "Service incident notification",
            ["We are aware of an incident impacting some customers."],
            ["This is synthetic incident content for testing."],
            {"title": "Incident summary", "headers": ["Field", "Value"],
             "rows": [["ID", _rand_ref("INC")], ["Status", _pick(["Investigating", "Resolved"])]]}
        ),
        "service_acquisition_notice": (
            "Service acquisition notice",
            ["We are writing to inform you that our services will be transitioning to a new provider."],
            ["Synthetic notice for test environments only."],
            None
        ),
        "consultancy_quote": (
            "Consultancy quotation",
            ["Please find below a quotation for consultancy services."],
            [f"Quote reference: {_rand_ref('QUOTE')}", "Validity: 14 days (synthetic)."],
            {"title": "Quotation", "headers": ["Item", "Amount"],
             "rows": [["Discovery workshop", _money(300, 900)],
                      ["Implementation", _money(800, 9000)]]}
        ),
    }

    return templates.get(template, (
        "General notification",
        ["This is a synthetic notification generated for testing purposes."],
        ["Synthetic document - do not treat as real."],
        None
    ))
