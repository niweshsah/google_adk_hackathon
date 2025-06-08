from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict

@dataclass
class Transaction:
    id: str
    amount: float
    type: str  # "income" or "expense"
    category: str
    department: str
    description: str
    date: datetime
    status: str = "pending"

@dataclass
class Budget:
    department: str
    period: str  # "monthly", "quarterly", "annual"
    total_amount: float
    start_date: datetime
    end_date: datetime
    spent_amount: float = 0
    remaining_amount: float = field(init=False)

    def __post_init__(self):
        self.remaining_amount = self.total_amount - self.spent_amount

@dataclass
class Payment:
    id: str
    amount: float
    recipient: str
    purpose: str
    due_date: datetime
    status: str = "pending"
    payment_date: datetime = None

@dataclass
class Account:
    id: str
    name: str
    type: str  # "operating", "emergency", "investment"
    balance: float
    last_updated: datetime

class FinanceDB:
    def __init__(self):
        self.transactions: List[Transaction] = []
        self.budgets: Dict[str, Budget] = {
            "WardA": Budget(
                department="WardA",
                period="monthly",
                total_amount=50000.0,
                start_date=datetime(2025, 6, 1),
                end_date=datetime(2025, 6, 30),
                spent_amount=15000.0
            ),
            "WardB": Budget(
                department="WardB",
                period="monthly",
                total_amount=75000.0,
                start_date=datetime(2025, 6, 1),
                end_date=datetime(2025, 6, 30),
                spent_amount=25000.0
            ),
        }
        self.payments: List[Payment] = []
        self.accounts: Dict[str, Account] = {
            "main": Account(
                "main",
                "Operating Account",
                "operating",
                1000000.0,
                datetime.now()
            ),
            "emergency": Account(
                "emergency",
                "Emergency Fund",
                "emergency",
                500000.0,
                datetime.now()
            )
        }

# Global instance
finance_db = FinanceDB()