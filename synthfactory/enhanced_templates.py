from __future__ import annotations

import random
from faker import Faker
from .models import LetterDoc

fake = Faker("en_GB")

from .faker_gen import (
    _sort_code,
    _acc_no,
    _money,
    _date_str,
    _rand_future,
    _rand_past,
    _pick,
    make_person as _make_person,
    make_account as _make_account,
)

ENHANCED_TEMPLATES = {
    "bank_statement": (
        "Bank Statement",
        [
            f"Account: {_acc_no()}",
            f"Sort Code: {_sort_code()}",
            f"Period: {_date_str(_rand_past(30, 35))} to {_date_str(_rand_past(0, 5))}",
        ],
        [
            "Opening: £" + str(round(random.uniform(500, 3000), 2)),
            "Closing: £" + str(round(random.uniform(500, 3000), 2)),
        ],
        {
            "title": "Transactions",
            "headers": ["Date", "Description", "Amount"],
            "rows": [
                [
                    _date_str(_rand_past(1, 28)),
                    random.choice(["Tesco", "Amazon", "Salary"]),
                    _money(10, 200),
                ]
                for _ in range(5)
            ],
        },
    ),
    "credit_card": (
        "Credit Card Statement",
        [
            f"Card: **** {random.randint(1000, 9999)}",
            f"Due: {_date_str(_rand_future(14, 21))}",
        ],
        [
            f"Balance: £{random.randint(100, 2000)}",
            f"Min Payment: £{random.randint(20, 50)}",
        ],
        {
            "title": "Recent Transactions",
            "headers": ["Date", "Description", "Amount"],
            "rows": [
                [
                    _date_str(_rand_past(1, 25)),
                    random.choice(["Retail", "Online", "Restaurant"]),
                    _money(20, 300),
                ]
                for _ in range(4)
            ],
        },
    ),
    "passport": (
        "Passport Document",
        [f"Number: {random.randint(100000000, 999999999)}", f"Nationality: British"],
        [f"Valid Until: {_date_str(_rand_future(365, 3650))}"],
        {
            "title": "Details",
            "headers": ["Field", "Value"],
            "rows": [
                ["DOB", _date_str(fake.date_of_birth())],
                ["Sex", _pick(["M", "F"])],
            ],
        },
    ),
    "drivers_licence": (
        "Driving Licence",
        [
            f"Licence No: {random.randint(100000000, 999999999)}",
            f"Valid Until: {_date_str(_rand_future(365, 3650))}",
        ],
        ["Categories: " + _pick(["B", "B+E", "A, B, BE"])],
        {
            "title": "Licence Details",
            "headers": ["Field", "Value"],
            "rows": [
                ["DOB", _date_str(fake.date_of_birth())],
                ["Issue Date", _date_str(_rand_past(365, 3650))],
            ],
        },
    ),
    "utility_bill": (
        "Utility Bill",
        [
            f"Account: UT{random.randint(10000000, 99999999)}",
            f"Meter: EM{random.randint(100000, 999999)}",
        ],
        [f"Usage: {random.randint(100, 500)} kWh", f"Due: £{random.randint(50, 150)}"],
        {
            "title": "Usage",
            "headers": ["Period", "Reading", "Units"],
            "rows": [
                [
                    _date_str(_rand_past(30, 35)),
                    str(random.randint(10000, 15000)),
                    str(random.randint(100, 500)) + " kWh",
                ]
            ],
        },
    ),
    "mobile_bill": (
        "Mobile Phone Bill",
        [
            f"Number: +44 79{random.randint(10, 99)} {random.randint(100000, 999999)}",
            f"Due: {_date_str(_rand_future(7, 14))}",
        ],
        [f"Total Due: £{random.randint(20, 80)}"],
        {
            "title": "Charges",
            "headers": ["Type", "Amount"],
            "rows": [
                ["Plan", "£" + str(random.randint(15, 35))],
                ["Calls", "£" + str(random.randint(5, 20))],
                ["Texts", "£" + str(random.randint(2, 10))],
            ],
        },
    ),
    "insurance": (
        "Insurance Policy",
        [
            f"Policy: POL-{random.randint(1000000, 9999999)}",
            f"Cover: {_pick(['Buildings', 'Contents', 'Vehicle'])}",
        ],
        [
            f"Premium: £{random.randint(100, 500)}",
            f"Excess: £{random.choice(['100', '150', '200'])}",
        ],
        {
            "title": "Coverage",
            "headers": ["Item", "Sum Insured"],
            "rows": [
                ["Main Cover", "£" + str(random.randint(50000, 500000))],
                ["Contents", "£" + str(random.randint(10000, 100000))],
            ],
        },
    ),
    "payslip": (
        "Pay Slip",
        [
            f"Period: {_date_str(_rand_past(7, 14))} to {_date_str(_rand_past(0, 7))}",
            f"Pay Date: {_date_str(_rand_past(0, 3))}",
        ],
        [
            f"Net Pay: £{random.randint(1500, 4000)}",
            f"Tax Code: {_pick(['1257L', '1250L', '1275L'])}",
        ],
        {
            "title": "Earnings",
            "headers": ["Item", "Amount"],
            "rows": [
                ["Basic", "£" + str(random.randint(2000, 5000))],
                ["Tax", "£" + str(random.randint(300, 1000))],
                ["NI", "£" + str(random.randint(200, 500))],
            ],
        },
    ),
    "medical_card": (
        "Medical Health Card",
        [
            f"NHS: {random.randint(1000000000, 9999999999)}",
            f"GP: {fake.city()} Medical Centre",
        ],
        ["Present for NHS treatment."],
        {
            "title": "Details",
            "headers": ["Field", "Value"],
            "rows": [
                ["DOB", _date_str(fake.date_of_birth())],
                ["Blood", _pick(["A+", "O+", "B+", "AB+"])],
            ],
        },
    ),
    "gym_membership": (
        "Gym Membership",
        [
            f"Membership: GYM{random.randint(100000, 999999)}",
            f"Valid From: {_date_str(_rand_past(0, 30))}",
        ],
        [f"Monthly Fee: £{random.randint(20, 80)}"],
        {
            "title": "Membership",
            "headers": ["Type", "Value"],
            "rows": [
                ["Plan", _pick(["Standard", "Premium", "VIP"])],
                ["Trainer", _pick(["None", "Weekly", "Monthly"])],
            ],
        },
    ),
    "library_card": (
        "Library Card",
        [
            f"Card: LIB{random.randint(100000, 999999)}",
            f"Expiry: {_date_str(_rand_future(180, 730))}",
        ],
        ["Report lost card immediately."],
        {
            "title": "Account",
            "headers": ["Item", "Status"],
            "rows": [
                ["Loans", str(random.randint(1, 5))],
                ["Holds", str(random.randint(0, 3))],
            ],
        },
    ),
    "travel_insurance": (
        "Travel Insurance",
        [
            f"Policy: TRV-{random.randint(1000000, 9999999)}",
            f"Travel: {_date_str(_rand_future(7, 60))} to {_date_str(_rand_future(61, 90))}",
        ],
        [f"Premium: £{random.randint(20, 100)}"],
        {
            "title": "Cover",
            "headers": ["Item", "Limit"],
            "rows": [
                ["Medical", "£" + str(random.randint(1000000, 5000000))],
                ["Cancellation", "£" + str(random.randint(1000, 5000))],
            ],
        },
    ),
    "pet_insurance": (
        "Pet Insurance",
        [
            f"Policy: PET-{random.randint(1000000, 9999999)}",
            f"Pet: {fake.first_name()}",
        ],
        [f"Annual Premium: £{random.randint(100, 400)}"],
        {
            "title": "Cover",
            "headers": ["Item", "Limit"],
            "rows": [
                ["Vet Fees", "£" + str(random.randint(2000, 8000))],
                ["Liability", "£" + str(random.randint(1000000, 2000000))],
            ],
        },
    ),
    "car_valuation": (
        "Vehicle Valuation",
        [
            f"Reg: {random.choice(['ABC', 'DEF'])} {random.randint(10, 99)} {random.choice(['ABC', 'DEF'])}"
        ],
        [f"Value: £{random.randint(5000, 40000)}"],
        {
            "title": "Vehicle",
            "headers": ["Spec", "Value"],
            "rows": [
                ["Make", _pick(["Ford", "VW", "BMW"])],
                ["Model", _pick(["Focus", "Golf", "3 Series"])],
            ],
        },
    ),
    "employment_contract": (
        "Employment Contract",
        [
            f"Position: {_pick(['Developer', 'Manager', 'Analyst'])}",
            f"Start: {_date_str(_rand_future(1, 60))}",
        ],
        [f"Salary: £{random.randint(25000, 80000):,} pa"],
        {
            "title": "Terms",
            "headers": ["Item", "Detail"],
            "rows": [
                ["Hours", str(random.randint(35, 40)) + " hrs"],
                ["Leave", str(random.randint(20, 30)) + " days"],
            ],
        },
    ),
    "rental_agreement": (
        "Tenancy Agreement",
        [
            f"Property: {random.randint(1, 200)} {fake.street_name()}",
            f"Start: {_date_str(_rand_past(0, 30))}",
        ],
        [
            f"Rent: £{random.randint(600, 2000):,} pm",
            f"Deposit: £{random.randint(600, 2000):,}",
        ],
        {
            "title": "Tenancy",
            "headers": ["Term", "Value"],
            "rows": [
                ["Type", _pick(["AST", "Fixed Term"])],
                ["Furnished", _pick(["Yes", "No"])],
            ],
        },
    ),
    "store_card": (
        "Store Card Statement",
        [
            f"Account: SC{random.randint(10000000, 99999999)}",
            f"Due: {_date_str(_rand_future(5, 20))}",
        ],
        [f"Balance: £{random.randint(50, 500)}", f"APR: {random.randint(20, 35)}%"],
        {
            "title": "Summary",
            "headers": ["Item", "Value"],
            "rows": [
                ["Credit Limit", "£" + str(random.randint(500, 2500))],
                ["Min Payment", "£" + str(random.randint(15, 50))],
            ],
        },
    ),
    "membership_card": (
        "Membership Card",
        [
            f"ID: MEM{random.randint(100000, 999999)}",
            f"Valid: {_date_str(_rand_future(180, 730))}",
        ],
        ["Present at checkout."],
        {
            "title": "Membership",
            "headers": ["Tier", "Points"],
            "rows": [
                ["Level", _pick(["Gold", "Silver", "Bronze"])],
                ["Balance", str(random.randint(0, 50000))],
            ],
        },
    ),
}


def make_person():
    return _make_person()


def make_account(bank_name: str):
    return _make_account(bank_name)


def generate_enhanced_letter(doc_id: str, company_name: str, template: str):
    if template in ENHANCED_TEMPLATES:
        subject, paras, opt, table = ENHANCED_TEMPLATES[template]
        owner = make_person()
        acc = make_account(company_name)
        return LetterDoc(
            doc_id=doc_id,
            template=template,
            owner=owner,
            account=acc,
            issue_date=_rand_past(0, 25),
            subject=subject,
            body_paragraphs=paras,
            optional_lines=opt,
            table_title=table.get("title") if table else None,
            table_headers=table.get("headers") if table else None,
            table_rows=table.get("rows") if table else None,
            display_sort_code=acc.sort_code,
            display_account_number=acc.account_number,
        )
    return None


def get_enhanced_template_names():
    return list(ENHANCED_TEMPLATES.keys())
