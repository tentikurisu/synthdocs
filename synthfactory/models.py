from __future__ import annotations
from datetime import date
from pydantic import BaseModel, Field
from typing import Any

class Person(BaseModel):
    full_name: str
    address_lines: list[str]
    city: str
    postcode: str

class Account(BaseModel):
    sort_code: str
    account_number: str
    bank_name: str | None = None

class Transaction(BaseModel):
    txn_date: date
    description: str
    paid_in: float | None = None
    paid_out: float | None = None
    running_balance: float

class StatementDoc(BaseModel):
    doc_id: str
    owner: Person
    account: Account
    issue_date: date
    period_from: date
    period_to: date
    opening_balance: float
    closing_balance: float
    transactions: list[Transaction] = Field(default_factory=list)
    footer_notes: list[str] = Field(default_factory=list)

class LetterDoc(BaseModel):
    doc_id: str
    template: str
    owner: Person
    account: Account
    issue_date: date
    subject: str
    body_paragraphs: list[str] = Field(default_factory=list)
    optional_lines: list[str] = Field(default_factory=list)

    table_title: str | None = None
    table_headers: list[str] | None = None
    table_rows: list[list[str]] | None = None

    display_sort_code: str | None = None
    display_account_number: str | None = None

class GroundTruthField(BaseModel):
    value: Any
    visible: bool = True

class GroundTruth(BaseModel):
    doc_type: str
    doc_id: str
    fields: dict[str, GroundTruthField]
    meta: dict[str, Any] = Field(default_factory=dict)
