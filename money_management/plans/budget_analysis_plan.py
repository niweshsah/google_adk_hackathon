from google.adk.planning import BasePlan
from ..tools import BudgetTool, ExpenseAnalyticsTool

class BudgetAnalysisPlan(BasePlan):
    def __init__(self):
        super().__init__(
            name="budget_analysis",
            description="Analyze department budgets and spending patterns"
        )
        self.budget_tool = BudgetTool(
            name="budget_check",
            description="Check department budget status"
        )
        self.analytics_tool = ExpenseAnalyticsTool(
            name="expense_analysis",
            description="Analyze expense patterns"
        )
    
    async def execute(self, department: str):
        budget_status = await self.budget_tool.run(department=department)
        spending_analysis = await self.analytics_tool.run(
            period="month",
            department=department
        )
        
        return {
            "budget_status": budget_status,
            "spending_analysis": spending_analysis
        }