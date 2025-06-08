from google.adk.tools import BaseTool
from datetime import datetime
from ..models import finance_db, Transaction

class TransactionTool(BaseTool):
    def __init__(self, *, name: str, description: str):
        super().__init__(name=name, description=description)
    
    async def run(self, amount: float, type: str, category: str, 
                 department: str, description: str) -> dict:
        try:
            transaction = Transaction(
                id=str(datetime.now().timestamp()),
                amount=amount,
                type=type,
                category=category,
                department=department,
                description=description,
                date=datetime.now()
            )
            finance_db.transactions.append(transaction)
            return {
                "status": "success",
                "message": f"Transaction recorded: {amount} for {category}"
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}