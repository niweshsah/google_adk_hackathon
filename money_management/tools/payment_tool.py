from google.adk.tools import BaseTool
from ..models import finance_db, Payment
from datetime import datetime

class PaymentTool(BaseTool):
    def __init__(self, *, name: str, description: str):
        super().__init__(name=name, description=description)
    
    async def run(self, amount: float, recipient: str, purpose: str, 
                 due_date: datetime) -> dict:
        try:
            payment = Payment(
                id=str(datetime.now().timestamp()),
                amount=amount,
                recipient=recipient,
                purpose=purpose,
                due_date=due_date
            )
            finance_db.payments.append(payment)
            return {
                "status": "success",
                "message": f"Payment scheduled: {amount} to {recipient}"
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}