"""
Money Management System Agent Module
Rule-based implementation for hospital financial operations.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any
from .tools import (
    TransactionTool,
    BudgetTool,
    ExpenseAnalyticsTool,
    PaymentTool,
    BalanceTool
)
from .models import finance_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MoneyManagementSystem:
    """Rule-based system for managing hospital finances and budgets."""

    def __init__(self):
        # Initialize tools
        self.tools = {
            "balance": BalanceTool(
                name="check_balance",
                description="Check account balances"
            ),
            "transaction": TransactionTool(
                name="record_transaction",
                description="Record income or expense transactions"
            ),
            "budget": BudgetTool(
                name="manage_budget",
                description="Handle budget-related operations"
            ),
            "payment": PaymentTool(
                name="process_payment",
                description="Process and record payments"
            ),
            "analytics": ExpenseAnalyticsTool(
                name="expense_analytics",
                description="Analyze spending patterns"
            )
        }
        logger.info("Money Management System initialized")

    async def process_query(self, query: str) -> Dict[str, Any]:
        """Process queries using rule-based matching"""
        query = query.lower().strip()
        
        try:
            # Balance checks
            if any(word in query for word in ["balance", "account", "funds"]):
                if "emergency" in query:
                    result = await self.tools["balance"].run(account="emergency")
                else:
                    result = await self.tools["balance"].run(account="main")
                return {"status": "success", "response": result}

            # Budget operations
            elif any(word in query for word in ["budget", "allocation", "spending limit"]):
                # Fix department name handling
                department = next((word.upper() for word in query.split() 
                                  if "ward" in word.lower()), None)
                
                if department:
                    # Convert to correct format (WardA, WardB)
                    if department != "GENERAL":
                        department = f"Ward{department[-1]}"  # Convert WARDA to WardA
                    
                    if department in finance_db.budgets:
                        budget = finance_db.budgets[department]
                        result = {
                            "department": department,
                            "total": budget.total_amount,
                            "spent": budget.spent_amount,
                            "remaining": budget.remaining_amount,
                            "period": budget.period
                        }
                        return {"status": "success", "response": result}
                    return {"status": "error", "response": f"No budget found for {department}"}
                return {"status": "error", "response": "Please specify a department/ward"}

            # Transaction recording
            elif any(word in query for word in ["record", "transaction", "expense", "income"]):
                # Parse amount from query
                amount = float(next((word for word in query.split() if word.replace('.','').isdigit()), 0))
                if amount == 0:
                    return {"status": "error", "response": "Please specify an amount"}
                
                transaction_type = "expense" if "expense" in query else "income"
                
                # Fix department name handling
                department = next((word.upper() for word in query.split() 
                                  if "ward" in word.lower()), "GENERAL")
                
                # Convert department name to correct format (WardA, WardB)
                if department != "GENERAL":
                    department = f"Ward{department[-1]}"  # Convert WARDA to WardA
                
                # First, verify the department exists
                if department != "GENERAL" and department not in finance_db.budgets:
                    return {"status": "error", "response": f"Department {department} not found"}
                
                # Record transaction
                result = await self.tools["transaction"].run(
                    amount=amount,
                    type=transaction_type,
                    category="general",
                    department=department,
                    description=query
                )
                
                # Update budget and account balance
                if result["status"] == "success":
                    if transaction_type == "expense":
                        # Update department budget
                        if department in finance_db.budgets:
                            finance_db.budgets[department].spent_amount += amount
                            finance_db.budgets[department].remaining_amount -= amount
                        
                        # Update main account balance
                        finance_db.accounts["main"].balance -= amount
                    else:  # income
                        # Update main account balance
                        finance_db.accounts["main"].balance += amount
                
                return {"status": "success", "response": f"Transaction recorded and budgets updated: {amount} ({transaction_type}) for {department}"}

            # Payment processing
            elif any(word in query for word in ["payment", "pay", "transfer"]):
                amount = float(next((word for word in query.split() if word.replace('.','').isdigit()), 0))
                if amount == 0:
                    return {"status": "error", "response": "Please specify payment amount"}
                
                # Check if we have sufficient balance
                if finance_db.accounts["main"].balance < amount:
                    return {"status": "error", "response": "Insufficient funds in main account"}
                
                result = await self.tools["payment"].run(
                    amount=amount,
                    recipient="vendor",
                    purpose=query,
                    due_date=datetime.now()
                )
                
                # Update account balance after payment
                if result["status"] == "success":
                    finance_db.accounts["main"].balance -= amount
                    finance_db.accounts["main"].last_updated = datetime.now()
                
                return {"status": "success", "response": f"Payment processed and balance updated: ${amount:,.2f}"}

            # Analytics and reports
            elif any(word in query for word in ["analytics", "analysis", "report", "summary"]):
                department = next((word for word in query.split() if "ward" in word.lower()), None)
                period = "month" if "month" in query else "week"
                
                result = await self.tools["analytics"].run(
                    period=period,
                    department=department
                )
                return {"status": "success", "response": result}

            # List wards or departments
            elif any(word in query for word in ["wards", "departments", "list wards"]):
                result = await self.list_wards()
                return result

            else:
                return {
                    "status": "error",
                    "response": "Unknown command. Available operations:\n" +
                              "1. Check balance\n" +
                              "2. Record transaction\n" +
                              "3. Check/update budget\n" +
                              "4. Process payment\n" +
                              "5. Generate analytics"
                }

        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {"status": "error", "response": str(e)}

    async def display_status(self):
        """Display current system status"""
        try:
            print("=" * 50)
            print(" Hospital Money Management System")
            print("-" * 50)
            print(f" Main Account: ${finance_db.accounts['main'].balance:,.2f}")
            print(f" Emergency Fund: ${finance_db.accounts['emergency'].balance:,.2f}")
            print("-" * 50)
            print(" Available Commands:")
            print(" - check balance")
            print(" - record expense/income <amount> for <department>")
            print(" - check budget <department>")
            print(" - process payment <amount>")
            print(" - show analytics [department] [period]")
            print("-" * 50)
            print(" (Type 'exit' to quit)")
            print("=" * 50)
        except Exception as e:
            logger.error(f"Error displaying status: {e}")
            raise

    # Add this method to the MoneyManagementSystem class
    async def list_wards(self) -> Dict[str, Any]:
        """List all available wards with their budget information"""
        try:
            wards = finance_db.budgets.keys()
            ward_info = {}
            for ward in wards:
                budget = finance_db.budgets[ward]
                ward_info[ward] = {
                    "total_budget": budget.total_amount,
                    "spent": budget.spent_amount,
                    "remaining": budget.remaining_amount
                }
            return {
                "status": "success",
                "response": ward_info
            }
        except Exception as e:
            logger.error(f"Error listing wards: {e}")
            return {
                "status": "error",
                "response": str(e)
            }

# Create singleton instances
money_system = MoneyManagementSystem()
root_agent = money_system  # Export the money_system instance as root_agent

async def main():
    """Main entry point with example queries"""
    try:
        await money_system.display_status()
        
        while True:
            try:
                query = input("\nQuery> ").strip()
                if query.lower() in ['exit', 'quit']:
                    break
                
                result = await money_system.process_query(query)
                if result["status"] == "success":
                    print(f"\nResponse: {result['response']}")
                else:
                    print(f"\nError: {result['response']}")
                    
            except KeyboardInterrupt:
                print("\nGracefully shutting down...")
                break
            except Exception as e:
                logger.error(f"Error: {e}")
                print(f"Error: {str(e)}")
    
    except Exception as e:
        logger.error(f"System error: {e}")
        raise

def run_agent():
    """Helper function to run the agent"""
    asyncio.run(main())

if __name__ == "__main__":
    run_agent()