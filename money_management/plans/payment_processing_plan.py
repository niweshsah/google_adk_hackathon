from google.adk.planning import BasePlan
from ..tools import PaymentTool, TransactionTool
from datetime import datetime

class PaymentProcessingPlan(BasePlan):
    def __init__(self):
        super().__init__(
            name="payment_processing",
            description="Process payments and record transactions"
        )
        self.payment_tool = PaymentTool(
            name="process_payment",
            description="Process payment requests"
        )
        self.transaction_tool = TransactionTool(
            name="record_transaction",
            description="Record payment transactions"
        )
    
    async def execute(self, amount: float, recipient: str, 
                     purpose: str, department: str):
        # Schedule payment
        payment_result = await self.payment_tool.run(
            amount=amount,
            recipient=recipient,
            purpose=purpose,
            due_date=datetime.now()
        )
        
        # Record transaction
        if payment_result["status"] == "success":
            transaction_result = await self.transaction_tool.run(
                amount=amount,
                type="expense",
                category="payment",
                department=department,
                description=f"Payment to {recipient} for {purpose}"
            )
            return {
                "payment": payment_result,
                "transaction": transaction_result
            }
        return payment_result