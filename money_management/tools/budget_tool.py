from google.adk.tools import BaseTool
from ..models import finance_db

class BudgetTool(BaseTool):
    def __init__(self, *, name: str, description: str):
        super().__init__(name=name, description=description)
    
    async def run(self, department: str, action: str = "check", 
                 amount: float = None) -> dict:
        budget = finance_db.budgets.get(department)
        if not budget:
            return {"status": "error", "message": f"No budget for {department}"}
            
        if action == "check":
            return {
                "status": "success",
                "data": {
                    "total": budget.total_amount,
                    "spent": budget.spent_amount,
                    "remaining": budget.remaining_amount
                }
            }
        elif action == "update":
            budget.spent_amount += amount
            budget.remaining_amount = budget.total_amount - budget.spent_amount
            return {"status": "success", "message": "Budget updated"}