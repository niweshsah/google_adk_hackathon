from google.adk.tools import BaseTool
from ..models import finance_db
from datetime import datetime, timedelta

class ExpenseAnalyticsTool(BaseTool):
    def __init__(self, *, name: str, description: str):
        super().__init__(name=name, description=description)
    
    async def run(self, period: str = "month", department: str = None) -> dict:
        start_date = datetime.now() - timedelta(days=30 if period == "month" else 7)
        
        transactions = [t for t in finance_db.transactions 
                       if t.date >= start_date and 
                       (department is None or t.department == department)]
        
        total_spent = sum(t.amount for t in transactions if t.type == "expense")
        total_income = sum(t.amount for t in transactions if t.type == "income")
        
        return {
            "status": "success",
            "data": {
                "period": period,
                "total_spent": total_spent,
                "total_income": total_income,
                "transaction_count": len(transactions)
            }
        }