"""
Ingestion router — SMS parsing and statement uploads (CSV/PDF).
"""

from __future__ import annotations

import csv
import io
import importlib
import math
import re
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
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

DATE_KEYS = [
    "date",
    "transaction date",
    "txn date",
    "value date",
    "posting date",
]

DESCRIPTION_KEYS = [
    "description",
    "narration",
    "particulars",
    "remarks",
    "details",
    "transaction details",
    "transaction remarks",
]

AMOUNT_KEYS = [
    "amount",
    "transaction amount",
    "txn amount",
    "amt",
    "value",
]

DEBIT_KEYS = [
    "debit",
    "debit amount",
    "debit amt",
    "withdrawal",
    "withdrawal amount",
    "withdrawal amt",
    "dr amount",
    "paid out",
]

CREDIT_KEYS = [
    "credit",
    "credit amount",
    "credit amt",
    "deposit",
    "deposit amount",
    "deposit amt",
    "cr amount",
    "paid in",
]

TYPE_KEYS = ["transaction type", "type", "dr cr", "drcr"]
MERCHANT_KEYS = ["merchant", "payee", "beneficiary"]
MODE_KEYS = ["payment mode", "mode", "channel", "transaction mode"]
HEADER_HINTS = ["date", "description", "narration", "particular", "debit", "credit", "withdrawal", "deposit", "amount", "balance"]


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

    merchant = _extract_merchant_from_description(message)

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


def _transaction_from_record(record: dict[str, Any]) -> ParsedTransaction:
    normalized = _normalize_record(record)

    timestamp_raw = _pick_record_value(normalized, DATE_KEYS)
    timestamp = _coerce_timestamp(timestamp_raw)

    description = _coerce_optional_text(_pick_record_value(normalized, DESCRIPTION_KEYS))

    merchant = _coerce_optional_text(_pick_record_value(normalized, MERCHANT_KEYS))
    if not merchant:
        merchant = _extract_merchant_from_description(description)

    tx_type_raw = _coerce_optional_text(_pick_record_value(normalized, TYPE_KEYS), lower=True)
    explicit_category = _coerce_optional_text(
        _pick_record_value(normalized, ["category"]),
        lower=True,
        underscored=True,
    )

    amount, inferred_type = _extract_amount_and_type(normalized)
    tx_type = "credit" if (tx_type_raw == "credit" or inferred_type == "credit") else "debit"

    payment_mode_raw = _pick_record_value(normalized, MODE_KEYS)
    payment_mode = _coerce_optional_text(payment_mode_raw, default=None, lower=True, underscored=True)
    if not payment_mode:
        payment_mode = _infer_payment_mode(description)

    category_text = explicit_category or _infer_category((description or merchant or "others"))
    category = category_text if category_text else "others"

    return ParsedTransaction(
        amount=round(amount, 2),
        category=category,
        merchant=merchant,
        transaction_type=tx_type,
        payment_mode=payment_mode,
        timestamp=timestamp.isoformat(),
        description=description,
    )


def _normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in record.items():
        normalized[_normalize_key(key)] = value
    return normalized


def _normalize_key(value: Any) -> str:
    text = str(value).strip().lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _pick_record_value(record: dict[str, Any], keys: list[str]) -> Any:
    normalized_keys = [_normalize_key(key) for key in keys]

    for key in keys:
        if key in record:
            return record[key]

    for alias in normalized_keys:
        for record_key, value in record.items():
            if record_key == alias:
                return value

    for alias in normalized_keys:
        for record_key, value in record.items():
            if alias and (alias in record_key or record_key in alias):
                return value

    return None


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    if isinstance(value, str):
        text = value.strip().lower()
        if not text:
            return True
        if text in {"-", "--", "na", "n/a", "null", "none", "nil"}:
            return True
    return False


def _coerce_optional_text(
    value: Any,
    default: Optional[str] = None,
    lower: bool = False,
    underscored: bool = False,
) -> Optional[str]:
    if _is_empty(value):
        return default

    text = str(value).strip()
    if lower:
        text = text.lower()
    if underscored:
        text = text.replace(" ", "_")

    return text or default


def _coerce_amount(value: Any) -> float:
    if isinstance(value, (int, float)):
        return round(float(value), 2)

    text = str(value).strip().lower()
    if not text or text in {"-", "--", "na", "n/a", "null", "none", "nil"}:
        raise ValueError("Missing amount")

    sign_hint = 0
    if text.startswith("(") and text.endswith(")"):
        sign_hint = -1
        text = text[1:-1]

    if " dr" in f" {text}" or text.endswith("dr"):
        sign_hint = -1
    elif " cr" in f" {text}" or text.endswith("cr"):
        sign_hint = 1

    text = text.replace("₹", "").replace("inr", "")
    text = text.replace("dr", "").replace("cr", "")
    text = text.replace(",", "").strip()

    numeric = re.sub(r"[^0-9.\-]", "", text)
    if not numeric or numeric in {"-", ".", "-."}:
        raise ValueError("Missing amount")

    amount = float(numeric)
    if sign_hint != 0 and amount > 0:
        amount *= sign_hint

    return round(amount, 2)


def _coerce_timestamp(value: Any) -> datetime:
    if _is_empty(value):
        return datetime.utcnow()

    if isinstance(value, datetime):
        return value

    if hasattr(value, "to_pydatetime"):
        try:
            as_dt = value.to_pydatetime()
            if isinstance(as_dt, datetime):
                return as_dt
        except Exception:
            pass

    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue

    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return datetime.utcnow()


def _extract_amount_and_type(record: dict[str, Any]) -> tuple[float, str]:
    amount_raw = _pick_record_value(record, AMOUNT_KEYS)
    if not _is_empty(amount_raw):
        amount = _coerce_amount(amount_raw)
        if amount < 0:
            return abs(amount), "debit"
        return amount, "debit"

    debit_raw = _pick_record_value(record, DEBIT_KEYS)
    credit_raw = _pick_record_value(record, CREDIT_KEYS)

    debit_amount = None if _is_empty(debit_raw) else _coerce_amount(debit_raw)
    credit_amount = None if _is_empty(credit_raw) else _coerce_amount(credit_raw)

    if debit_amount and debit_amount > 0:
        return abs(debit_amount), "debit"
    if credit_amount and credit_amount > 0:
        return abs(credit_amount), "credit"

    raise ValueError("Missing amount/debit/credit columns")


def _extract_merchant_from_description(description: Optional[str]) -> Optional[str]:
    if not description:
        return None

    cleaned = re.sub(r"\s+", " ", description).strip()
    if not cleaned:
        return None

    upi_match = re.search(
        r"UPI/(?:CR|DR)/[^/]+/(?P<merchant>.+?)/[A-Z0-9]{3,6}(?:/|$)",
        cleaned,
        flags=re.IGNORECASE,
    )
    if upi_match:
        upi_merchant = _clean_merchant_candidate(upi_match.group("merchant"))
        if upi_merchant:
            return upi_merchant

    # Bank narrations often end with AT <branch/address>; this is location, not merchant.
    cleaned = re.sub(
        r"\bAT\s+\d{1,8}\s+[A-Za-z0-9 .,&'_-]+$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()

    # Try common patterns first.
    match = re.search(r"(?:to|via)\s+([A-Za-z0-9 .,&'_-]{3,60})", cleaned, flags=re.IGNORECASE)
    if match:
        merchant = _clean_merchant_candidate(match.group(1))
        if merchant:
            return merchant

    # For slash-delimited statements, pick the first human-like segment after skipping tokens/noise.
    for segment in [part.strip() for part in cleaned.split("/") if part and part.strip()]:
        if re.fullmatch(r"[A-Za-z]{1,3}", segment):
            continue
        if re.search(r"\b(?:upi|dep|wdl|tfr|pay|paym|payment|txn|trf|cr|dr)\b", segment, flags=re.IGNORECASE):
            continue

        merchant = _clean_merchant_candidate(segment)
        if merchant and len(re.sub(r"[^A-Za-z]", "", merchant)) >= 3:
            return merchant

    return _clean_merchant_candidate(cleaned[:60])


def _clean_merchant_candidate(value: Optional[str]) -> Optional[str]:
    if not value:
        return None

    text = re.sub(r"\s+", " ", str(value)).strip(" .,:;-_/")
    if not text:
        return None

    text = re.sub(r"\b(?:pay|paym|payment)\s+\d+[A-Za-z0-9]*$", "", text, flags=re.IGNORECASE).strip(" .,:;-_/")
    if not text:
        return None

    # Reject obvious location-like values (e.g., "15901 SARDAR PATEL NAGAR").
    if re.search(r"\d", text) and re.search(r"\b(?:nagar|colony|street|road|sector|phase|layout|area|city)\b", text, flags=re.IGNORECASE):
        return None

    if text.isdigit():
        return None

    return text[:60]


def _infer_payment_mode(description: Optional[str]) -> str:
    lower = (description or "").lower()
    if "upi" in lower or "vpa" in lower:
        return "upi"
    if "card" in lower or "pos" in lower:
        return "card"
    if "neft" in lower:
        return "neft"
    if "imps" in lower:
        return "imps"
    if "rtgs" in lower:
        return "rtgs"
    if "atm" in lower:
        return "atm"
    return "bank"


def _parse_csv_content(content: bytes) -> list[ParsedTransaction]:
    decoded = content.decode("utf-8-sig", errors="ignore")
    reader = csv.DictReader(io.StringIO(decoded))

    parsed: list[ParsedTransaction] = []
    for row in reader:
        try:
            parsed.append(_transaction_from_record(row))
        except Exception:
            continue

    return parsed


def _parse_excel_content(content: bytes, password: Optional[str] = None) -> list[ParsedTransaction]:
    try:
        pd = importlib.import_module("pandas")
    except Exception as exc:
        raise ValueError("Excel parsing dependencies are missing. Install pandas/openpyxl/xlrd.") from exc

    stream = io.BytesIO(content)
    is_encrypted = False

    try:
        msoffcrypto = importlib.import_module("msoffcrypto")
        office_file = msoffcrypto.OfficeFile(io.BytesIO(content))
        is_encrypted = bool(office_file.is_encrypted())

        if is_encrypted:
            if not password:
                raise ValueError("Excel statement is password-protected. Provide statement password.")

            office_file.load_key(password=password)
            decrypted = io.BytesIO()
            office_file.decrypt(decrypted)
            decrypted.seek(0)
            stream = decrypted
    except ModuleNotFoundError:
        if password:
            raise ValueError("Excel password support is unavailable. Install msoffcrypto-tool.")
    except ValueError:
        raise
    except Exception as exc:
        if is_encrypted or password:
            raise ValueError("Unable to unlock Excel statement. Please check the statement password.") from exc

    try:
        excel_file = pd.ExcelFile(stream)
    except Exception:
        excel_file = None

    parsed_by_sheet: list[ParsedTransaction] = []

    if excel_file is not None:
        for sheet_name in excel_file.sheet_names:
            try:
                stream.seek(0)
                df = _read_excel_dataframe(pd, stream, sheet_name=sheet_name)
            except Exception:
                continue

            if getattr(df, "empty", True):
                continue

            records = df.to_dict(orient="records")
            parsed: list[ParsedTransaction] = []
            for row in records:
                try:
                    parsed.append(_transaction_from_record(row))
                except Exception:
                    continue

            if len(parsed) > len(parsed_by_sheet):
                parsed_by_sheet = parsed

        return parsed_by_sheet

    try:
        stream.seek(0)
        df = _read_excel_dataframe(pd, stream, sheet_name=0)
    except Exception as exc:
        raise ValueError("Unable to read Excel statement. Please upload a valid .xls or .xlsx file.") from exc

    if getattr(df, "empty", True):
        return []

    records = df.to_dict(orient="records")
    parsed: list[ParsedTransaction] = []
    for row in records:
        try:
            parsed.append(_transaction_from_record(row))
        except Exception:
            continue

    return parsed


def _read_excel_dataframe(pd: Any, stream: io.BytesIO, sheet_name: Any = 0):
    # First try standard header parsing.
    stream.seek(0)
    df = pd.read_excel(stream, sheet_name=sheet_name, dtype=object)
    if not getattr(df, "empty", True):
        columns = [_normalize_key(col) for col in list(df.columns)]
        if _columns_look_like_statement(columns):
            return df

    # Fallback: detect header row from raw sheet with no predefined header.
    stream.seek(0)
    raw = pd.read_excel(stream, sheet_name=sheet_name, header=None, dtype=object)
    if getattr(raw, "empty", True):
        return raw

    header_row_idx = _detect_header_row(raw)
    if header_row_idx is None:
        return df

    header_values = [str(value).strip() for value in list(raw.iloc[header_row_idx].tolist())]
    data = raw.iloc[header_row_idx + 1 :].copy()
    data.columns = header_values
    data = data.dropna(how="all")
    return data


def _columns_look_like_statement(columns: list[str]) -> bool:
    text = " ".join(columns)
    score = 0
    for hint in ["date", "narration", "description", "particular", "debit", "credit", "withdrawal", "deposit", "amount"]:
        if hint in text:
            score += 1
    return score >= 2


def _detect_header_row(raw_df: Any) -> Optional[int]:
    max_rows = min(80, len(raw_df.index))
    best_idx = None
    best_score = -1

    for idx in range(max_rows):
        row_values = [
            _normalize_key(value)
            for value in list(raw_df.iloc[idx].tolist())
            if not _is_empty(value)
        ]
        if not row_values:
            continue

        row_text = " ".join(row_values)
        score = 0
        for hint in HEADER_HINTS:
            if hint in row_text:
                score += 1

        if score > best_score:
            best_score = score
            best_idx = idx

    if best_idx is None or best_score < 2:
        return None

    return int(best_idx)


def _parse_statement_content(
    file_name: str,
    content: bytes,
    password: Optional[str] = None,
) -> list[ParsedTransaction]:
    lower_name = file_name.lower()
    if lower_name.endswith(".csv"):
        return _parse_csv_content(content)
    if lower_name.endswith(".xls") or lower_name.endswith(".xlsx"):
        return _parse_excel_content(content, password=password)

    raise ValueError("Unsupported statement format. Upload .csv, .xls, or .xlsx.")


def _parse_pdf_content(content: bytes, password: Optional[str] = None) -> list[ParsedTransaction]:
    text = ""

    try:
        pypdf_module = importlib.import_module("pypdf")
        PdfReader = getattr(pypdf_module, "PdfReader")

        reader = PdfReader(io.BytesIO(content))
        if getattr(reader, "is_encrypted", False):
            if not password:
                raise ValueError("PDF is password-protected. Provide statement password.")

            decrypted = reader.decrypt(password)
            if decrypted in (0, False):
                raise ValueError("Unable to unlock PDF. Please check the statement password.")

        text = "\n".join((page.extract_text() or "") for page in reader.pages)
    except ValueError:
        raise
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
@router.post("/upload/statement", response_model=UploadResponse)
async def upload_csv_statement(
    file: UploadFile = File(...),
    password: Optional[str] = Form(default=None),
    persist: bool = Query(default=True),
    current_user: User = Depends(get_dashboard_user),
    session: AsyncSession = Depends(get_session),
):
    """Upload CSV/XLS/XLSX statement, parse rows, and optionally import transactions."""
    lower_name = file.filename.lower()
    if not (lower_name.endswith(".csv") or lower_name.endswith(".xls") or lower_name.endswith(".xlsx")):
        raise HTTPException(status_code=400, detail="Please upload a .csv, .xls, or .xlsx file")

    content = await file.read()
    try:
        parsed = _parse_statement_content(file.filename, content, password=password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not parsed:
        raise HTTPException(
            status_code=400,
            detail=(
                "No transactions detected. Ensure statement has date + amount columns "
                "or debit/credit columns with narration/description."
            ),
        )

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
    password: Optional[str] = Form(default=None),
    persist: bool = Query(default=False),
    current_user: User = Depends(get_dashboard_user),
    session: AsyncSession = Depends(get_session),
):
    """Upload PDF statement, extract transaction-like entries, and optionally import."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a .pdf file")

    content = await file.read()
    try:
        parsed = _parse_pdf_content(content, password=password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    imported = await _persist_transactions(session, current_user.id, parsed, source="pdf") if persist else 0

    return UploadResponse(
        file_name=file.filename,
        parsed_count=len(parsed),
        imported_count=imported,
        preview=parsed[:10],
    )
