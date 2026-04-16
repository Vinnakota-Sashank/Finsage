"""
Ingestion router — SMS parsing and statement uploads (CSV/PDF).
"""

from __future__ import annotations

import csv
import io
import importlib
import re
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

from app.database import get_session
from app.models.transaction import Transaction
from app.models.user import User
from app.routers.dashboard import get_dashboard_user

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


class ParsedTransaction(SQLModel):
    amount: float
    category: str
    merchant: Optional[str] = None
    transaction_type: str
    payment_mode: str
    timestamp: str
    description: Optional[str] = None


class SMSParseRequest(SQLModel):
    messages: list[str]


class SMSParseResponse(SQLModel):
    parsed_count: int
    transactions: list[ParsedTransaction]


class UploadResponse(SQLModel):
    file_name: str
    parsed_count: int
    imported_count: int
    preview: list[ParsedTransaction]


CATEGORY_HINTS = {
    "swiggy": "food_delivery",
    "zomato": "food_delivery",
    "uber": "transport",
    "ola": "transport",
    "amazon": "shopping",
    "flipkart": "shopping",
    "netflix": "subscriptions",
    "spotify": "subscriptions",
    "rent": "rent",
    "electricity": "utilities",
    "bill": "utilities",
    "sip": "sip_mutual_funds",
    "hospital": "health",
    "pharmacy": "health",
}


def _infer_category(text: str) -> str:
    lower = text.lower()
    for keyword, category in CATEGORY_HINTS.items():
        if keyword in lower:
            return category
    return "others"


def _parse_amount(text: str) -> Optional[float]:
    matches = re.findall(r"(?:₹|inr)\s*(\d+(?:,\d{3})*(?:\.\d+)?)", text.lower())
    if not matches:
        return None
    return float(matches[-1].replace(",", ""))


def _parse_timestamp(text: str) -> datetime:
    patterns = [
        r"(\d{4}-\d{2}-\d{2})",
        r"(\d{2}/\d{2}/\d{4})",
        r"(\d{2}-\d{2}-\d{4})",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if not match:
            continue
        raw = match.group(1)
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(raw, fmt)
            except ValueError:
                continue
    return datetime.utcnow()


def _parse_sms_message(message: str) -> Optional[ParsedTransaction]:
    amount = _parse_amount(message)
    if amount is None:
        return None

    lower = message.lower()
    is_debit = any(token in lower for token in ["debited", "debit", "spent", "sent", "paid"])
    is_credit = any(token in lower for token in ["credited", "credit", "received"])
    transaction_type = "debit" if is_debit or not is_credit else "credit"

    merchant_match = re.search(r"(?:at|to)\s+([a-zA-Z0-9 .&_-]{3,40})", message)
    merchant = merchant_match.group(1).strip() if merchant_match else None

    payment_mode = "upi" if "upi" in lower else "auto_debit" if "auto" in lower else "card" if "card" in lower else "bank"
    category = _infer_category(message if merchant is None else merchant)
    timestamp = _parse_timestamp(message)

    return ParsedTransaction(
        amount=round(amount, 2),
        category=category,
        merchant=merchant,
        transaction_type=transaction_type,
        payment_mode=payment_mode,
        timestamp=timestamp.isoformat(),
        description=message[:120],
    )


def _transaction_from_record(record: dict[str, str]) -> ParsedTransaction:
    amount_raw = record.get("amount") or record.get("Amount") or "0"
    amount = float(str(amount_raw).replace(",", ""))

    category = (record.get("category") or record.get("Category") or "others").strip().lower()
    merchant = (record.get("merchant") or record.get("Merchant") or "").strip() or None
    tx_type = (record.get("transaction_type") or record.get("type") or "debit").strip().lower()
    tx_type = "credit" if tx_type == "credit" else "debit"

    payment_mode = (record.get("payment_mode") or record.get("mode") or "manual").strip().lower()
    description = (record.get("description") or record.get("Description") or "").strip() or None

    timestamp_raw = (record.get("timestamp") or record.get("date") or record.get("Date") or "").strip()
    timestamp = datetime.utcnow()
    if timestamp_raw:
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d %H:%M:%S"):
            try:
                timestamp = datetime.strptime(timestamp_raw, fmt)
                break
            except ValueError:
                continue

    return ParsedTransaction(
        amount=round(amount, 2),
        category=category,
        merchant=merchant,
        transaction_type=tx_type,
        payment_mode=payment_mode,
        timestamp=timestamp.isoformat(),
        description=description,
    )


def _parse_pdf_content(content: bytes) -> list[ParsedTransaction]:
    text = ""

    try:
        pypdf_module = importlib.import_module("pypdf")
        PdfReader = getattr(pypdf_module, "PdfReader")

        reader = PdfReader(io.BytesIO(content))
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
    except Exception:
        # Fallback for environments without PDF parser.
        text = content.decode("latin1", errors="ignore")

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    parsed: list[ParsedTransaction] = []

    for line in lines:
        parsed_tx = _parse_sms_message(line)
        if parsed_tx:
            parsed.append(parsed_tx)

    return parsed


async def _persist_transactions(
    session: AsyncSession,
    user_id: int,
    transactions: list[ParsedTransaction],
    source: str,
) -> int:
    if not transactions:
        return 0

    for tx in transactions:
        session.add(
            Transaction(
                user_id=user_id,
                amount=tx.amount,
                category=tx.category,
                merchant=tx.merchant,
                description=tx.description,
                payment_mode=tx.payment_mode,
                transaction_type=tx.transaction_type,
                timestamp=datetime.fromisoformat(tx.timestamp),
                source=source,
            )
        )

    await session.commit()
    return len(transactions)


@router.get("/template/csv", response_model=dict)
async def get_csv_template_info():
    """Return expected CSV headers for statement upload."""
    return {
        "required_headers": ["amount", "category", "transaction_type"],
        "optional_headers": ["merchant", "payment_mode", "description", "timestamp"],
        "example": {
            "amount": "520.50",
            "category": "food_delivery",
            "transaction_type": "debit",
            "merchant": "Swiggy",
            "payment_mode": "upi",
            "description": "Lunch order",
            "timestamp": "2026-04-15",
        },
    }


@router.post("/sms/parse", response_model=SMSParseResponse)
async def parse_sms_messages(
    payload: SMSParseRequest,
):
    """Parse raw SMS texts into normalized transaction candidates."""
    parsed = [item for item in (_parse_sms_message(msg) for msg in payload.messages) if item is not None]
    return SMSParseResponse(parsed_count=len(parsed), transactions=parsed)


@router.post("/sms/import", response_model=UploadResponse)
async def import_sms_messages(
    payload: SMSParseRequest,
    persist: bool = Query(default=True),
    current_user: User = Depends(get_dashboard_user),
    session: AsyncSession = Depends(get_session),
):
    """Parse SMS messages and optionally persist them as transactions."""
    parsed = [item for item in (_parse_sms_message(msg) for msg in payload.messages) if item is not None]
    imported = await _persist_transactions(session, current_user.id, parsed, source="sms") if persist else 0
    return UploadResponse(
        file_name="sms_batch",
        parsed_count=len(parsed),
        imported_count=imported,
        preview=parsed[:10],
    )


@router.post("/upload/csv", response_model=UploadResponse)
async def upload_csv_statement(
    file: UploadFile = File(...),
    persist: bool = Query(default=True),
    current_user: User = Depends(get_dashboard_user),
    session: AsyncSession = Depends(get_session),
):
    """Upload CSV statement, parse rows, and optionally import transactions."""
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file")

    content = await file.read()
    decoded = content.decode("utf-8-sig", errors="ignore")
    reader = csv.DictReader(io.StringIO(decoded))

    parsed: list[ParsedTransaction] = []
    for row in reader:
        try:
            parsed.append(_transaction_from_record(row))
        except Exception:
            continue

    imported = await _persist_transactions(session, current_user.id, parsed, source="csv") if persist else 0

    return UploadResponse(
        file_name=file.filename,
        parsed_count=len(parsed),
        imported_count=imported,
        preview=parsed[:10],
    )


@router.post("/upload/pdf", response_model=UploadResponse)
async def upload_pdf_statement(
    file: UploadFile = File(...),
    persist: bool = Query(default=False),
    current_user: User = Depends(get_dashboard_user),
    session: AsyncSession = Depends(get_session),
):
    """Upload PDF statement, extract transaction-like entries, and optionally import."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a .pdf file")

    content = await file.read()
    parsed = _parse_pdf_content(content)
    imported = await _persist_transactions(session, current_user.id, parsed, source="pdf") if persist else 0

    return UploadResponse(
        file_name=file.filename,
        parsed_count=len(parsed),
        imported_count=imported,
        preview=parsed[:10],
    )
