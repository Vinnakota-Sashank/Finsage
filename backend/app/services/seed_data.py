"""
Seed data service — generates realistic synthetic financial data for user "Arjun Mehta".
This seeds the database for development/demo purposes.
"""

import random
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlalchemy import func

from app.models.user import User
from app.models.transaction import Transaction
from app.models.goal import Goal
from app.models.budget import Budget
from app.models.alert import Alert
from app.models.account import Account


# Categories with (base_amount, variance, payment_mode, is_recurring)
SPENDING_CATEGORIES = [
    ("rent", 22000, 0, "neft", True),
    ("groceries", 6500, 0.20, "upi", False),
    ("food_delivery", 5200, 0.25, "upi", False),
    ("dining_out", 3800, 0.30, "credit_card", False),
    ("transport", 4500, 0.20, "upi", False),
    ("shopping", 7000, 0.35, "credit_card", False),
    ("subscriptions", 1500, 0.05, "auto_debit", True),
    ("utilities", 3200, 0.10, "auto_debit", True),
    ("health", 1800, 0.40, "upi", False),
    ("education", 2000, 0.15, "credit_card", False),
    ("entertainment", 2500, 0.30, "upi", False),
    ("emi_student_loan", 8500, 0, "auto_debit", True),
    ("sip_mutual_funds", 15000, 0, "auto_debit", True),
    ("personal", 3000, 0.25, "upi", False),
]

FOOD_MERCHANTS = {
    "food_delivery": [("Swiggy", 0.45), ("Zomato", 0.35), ("Others", 0.20)],
    "dining_out": [("Restaurant", 0.50), ("Cafe", 0.30), ("Street Food", 0.20)],
    "groceries": [("BigBasket", 0.40), ("DMart", 0.35), ("Local Store", 0.25)],
}

# Keep seed volume high for hackathon demos (2,400+ yearly rows).
MONTHLY_TXN_FREQUENCY = {
    "groceries": (20, 32),
    "food_delivery": (24, 38),
    "dining_out": (16, 30),
    "transport": (40, 60),
    "shopping": (14, 28),
    "health": (8, 16),
    "education": (6, 12),
    "entertainment": (14, 26),
    "personal": (18, 30),
}


async def seed_demo_data(session: AsyncSession):
    """Seeds the database with Arjun Mehta's 12-month financial history."""

    # Check if data already exists
    existing = await session.execute(select(User).where(User.email == "arjun@example.com"))
    existing_user = existing.scalar_one_or_none()
    if existing_user is not None:
        tx_count_result = await session.execute(
            select(func.count(Transaction.id)).where(Transaction.user_id == existing_user.id)
        )
        existing_count = int(tx_count_result.scalar() or 0)

        min_target_transactions = 2400
        if existing_count >= min_target_transactions:
            return {"message": f"Demo data already exists ({existing_count} transactions)"}

        top_up_count = min_target_transactions - existing_count
        top_up_transactions = _generate_top_up_transactions(existing_user.id, top_up_count, datetime.utcnow())
        session.add_all(top_up_transactions)
        await session.commit()
        return {
            "message": (
                f"Backfilled demo data from {existing_count} to {existing_count + len(top_up_transactions)} transactions"
            )
        }

    # 1. Create user
    user = User(
        name="Arjun Mehta",
        email="arjun@example.com",
        phone="+919876543210",
        city="Hyderabad",
        occupation="Software Engineer",
        monthly_income=120000,
        tax_bracket=0.30,
        risk_appetite="moderate",
        auth_provider="local",
        hashed_password="demo",  # Not a real password, just for seed
    )
    session.add(user)
    await session.flush()

    # 2. Create bank account
    account = Account(
        user_id=user.id,
        bank_name="HDFC Bank",
        account_type="savings",
        account_number_masked="XXXX4521",
        balance=245000,
    )
    session.add(account)

    # 3. Generate 12 months of transactions
    now = datetime.utcnow()
    transactions = []

    for month_offset in range(12):
        month_date = now - timedelta(days=30 * (11 - month_offset))
        month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Monthly income
        transactions.append(Transaction(
            user_id=user.id,
            amount=120000,
            category="salary",
            subcategory="monthly_salary",
            merchant="Employer",
            description="Monthly salary credit",
            payment_mode="neft",
            transaction_type="credit",
            timestamp=month_start + timedelta(days=random.randint(0, 2)),
            is_recurring=True,
            source="seed",
        ))

        # Spending transactions
        for category, base, variance, mode, recurring in SPENDING_CATEGORIES:
            if recurring:
                # Single transaction for the month
                amount = base + random.uniform(-base * variance, base * variance)
                day = random.randint(1, 5) if category == "rent" else random.randint(1, 28)

                # Diwali spike in October
                if month_offset == 6 and category == "shopping":
                    amount *= 3.0
                if month_offset == 6 and category == "dining_out":
                    amount *= 1.5

                subcategory = None
                merchant = None
                if category in FOOD_MERCHANTS:
                    merchant_choice = random.choices(
                        [m[0] for m in FOOD_MERCHANTS[category]],
                        [m[1] for m in FOOD_MERCHANTS[category]]
                    )[0]
                    merchant = merchant_choice
                    subcategory = merchant_choice.lower().replace(" ", "_")

                transactions.append(Transaction(
                    user_id=user.id,
                    amount=round(amount, 2),
                    category=category,
                    subcategory=subcategory,
                    merchant=merchant,
                    description=f"{category.replace('_', ' ').title()} payment",
                    payment_mode=mode,
                    transaction_type="debit",
                    timestamp=month_start + timedelta(days=min(day, 28), hours=random.randint(8, 22)),
                    is_recurring=recurring,
                    source="seed",
                ))
            else:
                # Multiple smaller transactions through the month
                min_txn, max_txn = MONTHLY_TXN_FREQUENCY.get(category, (8, 16))
                num_txns = random.randint(min_txn, max_txn)
                total_for_category = base + random.uniform(-base * variance, base * variance)

                # Diwali spike
                if month_offset == 6 and category == "shopping":
                    total_for_category *= 3.0

                amounts = _split_amount(total_for_category, num_txns)
                for j, amt in enumerate(amounts):
                    day = random.randint(1, 28)

                    subcategory = None
                    merchant = None
                    if category in FOOD_MERCHANTS:
                        merchant_choice = random.choices(
                            [m[0] for m in FOOD_MERCHANTS[category]],
                            [m[1] for m in FOOD_MERCHANTS[category]]
                        )[0]
                        merchant = merchant_choice
                        subcategory = merchant_choice.lower().replace(" ", "_")

                    transactions.append(Transaction(
                        user_id=user.id,
                        amount=round(amt, 2),
                        category=category,
                        subcategory=subcategory,
                        merchant=merchant,
                        description=f"{category.replace('_', ' ').title()}",
                        payment_mode=mode,
                        transaction_type="debit",
                        timestamp=month_start + timedelta(days=day, hours=random.randint(8, 22), minutes=random.randint(0, 59)),
                        is_recurring=False,
                        source="seed",
                    ))

    min_target_transactions = 2400
    if len(transactions) < min_target_transactions:
        top_up_count = min_target_transactions - len(transactions)
        transactions.extend(_generate_top_up_transactions(user.id, top_up_count, now))

    session.add_all(transactions)

    # 4. Create goals
    goals = [
        Goal(user_id=user.id, name="Goa Trip", target_amount=50000, current_amount=32000,
             deadline=(now + timedelta(days=60)).date(), priority="high", probability=0.62),
        Goal(user_id=user.id, name="Emergency Fund", target_amount=360000, current_amount=245000,
             deadline=(now + timedelta(days=240)).date(), priority="high", probability=0.78),
        Goal(user_id=user.id, name="New Laptop", target_amount=120000, current_amount=45000,
             deadline=(now + timedelta(days=120)).date(), priority="medium", probability=0.34),
    ]
    session.add_all(goals)

    # 5. Create budgets
    budgets = [
        Budget(user_id=user.id, category="food_delivery", monthly_limit=6000),
        Budget(user_id=user.id, category="dining_out", monthly_limit=8000, alert_threshold=0.9),
        Budget(user_id=user.id, category="shopping", monthly_limit=8000),
        Budget(user_id=user.id, category="entertainment", monthly_limit=3000),
    ]
    session.add_all(budgets)

    # 6. Create sample alerts
    alerts = [
        Alert(
            user_id=user.id, severity="critical", alert_type="spending_spike",
            title="Unusual Spending Spike Detected",
            description="Shopping spend this week: ₹12,400 — that's 3.1× your weekly average of ₹4,000. Primary transactions: Amazon ₹6,200, Flipkart ₹4,800.",
            recommendation="Review your recent shopping transactions and consider setting a weekly budget.",
        ),
        Alert(
            user_id=user.id, severity="warning", alert_type="credit_health",
            title="Credit Utilization Rising",
            description="Credit card utilization at 68% (₹24,000 / ₹35,000 limit). Credit scores typically drop when utilization exceeds 30%.",
            recommendation="Pay ₹15,000 before March 20 billing cycle to bring utilization under 30%.",
        ),
        Alert(
            user_id=user.id, severity="warning", alert_type="budget_breach",
            title="Dining Budget Almost Exhausted",
            description="Dining budget: ₹7,400 / ₹8,000 used (92%) with 11 days remaining this month.",
            recommendation="Limit dining expenses for the rest of the month or adjust your budget.",
        ),
        Alert(
            user_id=user.id, severity="info", alert_type="recurring_anomaly",
            title="Upcoming Auto-Debit",
            description="SIP auto-debit of ₹15,000 scheduled for tomorrow. Current savings account balance: ₹2,45,000 — sufficient.",
            recommendation="No action needed. Balance is sufficient for the debit.",
        ),
        Alert(
            user_id=user.id, severity="insight", alert_type="recurring_anomaly",
            title="Missing Recurring Transaction",
            description="Netflix subscription (₹649) was not charged this billing cycle. Last charge: Feb 10.",
            recommendation="Check if your subscription was cancelled or if the linked card expired.",
        ),
        Alert(
            user_id=user.id, severity="warning", alert_type="goal_risk",
            title="Goal At Risk",
            description="Goa Trip savings: At current savings rate, projected to reach ₹46,200 by June — ₹3,800 short of ₹50,000 target.",
            recommendation="Increase monthly savings by ₹2,000 or reduce discretionary spending.",
        ),
    ]
    session.add_all(alerts)

    await session.commit()
    return {"message": f"Seeded {len(transactions)} transactions, {len(goals)} goals, {len(budgets)} budgets, {len(alerts)} alerts"}


def _split_amount(total: float, n: int) -> list[float]:
    """Split a total amount into n roughly proportional random parts."""
    weights = [random.random() for _ in range(n)]
    weight_sum = sum(weights)
    return [total * w / weight_sum for w in weights]


def _generate_top_up_transactions(user_id: int, top_up_count: int, now: datetime) -> list[Transaction]:
    """Generate additional micro transactions so yearly seed volume reaches target."""
    top_up_categories = ["transport", "food_delivery", "groceries", "personal"]
    generated: list[Transaction] = []

    for _ in range(top_up_count):
        category = random.choice(top_up_categories)
        month_offset = random.randint(0, 11)
        month_date = now - timedelta(days=30 * month_offset)
        month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        day = random.randint(1, 28)

        merchant = None
        subcategory = None
        if category in FOOD_MERCHANTS:
            merchant_choice = random.choices(
                [m[0] for m in FOOD_MERCHANTS[category]],
                [m[1] for m in FOOD_MERCHANTS[category]],
            )[0]
            merchant = merchant_choice
            subcategory = merchant_choice.lower().replace(" ", "_")

        generated.append(
            Transaction(
                user_id=user_id,
                amount=round(random.uniform(80, 650), 2),
                category=category,
                subcategory=subcategory,
                merchant=merchant,
                description=f"{category.replace('_', ' ').title()} quick expense",
                payment_mode="upi",
                transaction_type="debit",
                timestamp=month_start + timedelta(days=day, hours=random.randint(8, 23), minutes=random.randint(0, 59)),
                is_recurring=False,
                source="seed",
            )
        )

    return generated
