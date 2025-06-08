from google.adk.tools import BaseTool
from ..models import finance_db

class BalanceTool(BaseTool):
    def __init__(self, *, name: str, description: str):
        super().__init__(name=name, description=description)
    
    async def run(self, account: str = "main") -> dict:
        try:
            account_data = finance_db.accounts.get(account)
            if not account_data:
                return {
                    "status": "error",
                    "message": f"Account {account} not found"
                }
            
            return {
                "status": "success",
                "data": {
                    "account": account_data.name,
                    "balance": account_data.balance,
                    "last_updated": account_data.last_updated
                }
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}