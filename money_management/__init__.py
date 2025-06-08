"""
Money Management System for Hospital Finances
A module for managing hospital finances, budgets, and transactions.
"""

from .agent import MoneyManagementSystem, money_system
from .models import Transaction, Budget, Payment, Account, FinanceDB, finance_db

__version__ = "0.1.0"
__author__ = "Your Name"

__all__ = [
    'MoneyManagementSystem',
    'money_system',  # Export money_system instead of root_agent
    'Transaction',
    'Budget',
    'Payment',
    'Account',
    'FinanceDB',
    'finance_db'
]