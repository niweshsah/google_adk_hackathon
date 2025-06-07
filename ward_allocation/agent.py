# agent.py - Enhanced Ward Management Agent
import asyncio
from google.adk.agents import LlmAgent

# Import tools
from tools import (
    AvailabilityTool,
    AssignmentTool,
    DischargeTool,
    TransferTool,
    AnalyticsTool
)

# Import hospital database
from models import hospital_db

class WardManagementSystem:
    """Advanced AI system for managing ward allocations, discharges, transfers, and analytics."""

    def __init__(self):
        self.hospital_db = hospital_db
        self.root_agent = self._create_ward_agent()

    def _create_ward_agent(self):
        """Create the LLM-powered intelligent ward management agent"""
        return LlmAgent(
            name="enhanced_ward_manager",
            model="gemini-2.0-flash-exp",
            description="Advanced AI ward agent for handling hospital ward allocations, discharges, transfers, and analytics through natural conversation",
            instruction="""
You are an advanced hospital ward manager with strong conversational intelligence.

You can understand both casual and formal requests, such as:
- "Is there a bed in Ward A?"
- "Move Bob to Ward B"
- "Discharge patient 103"
- "How full is the hospital?"

You excel at:
- Interpreting natural language queries
- Handling ambiguity and following up for clarity
- Providing empathetic and helpful responses
- Automatically selecting the right tool for the task

🔧 TOOL USE INSTRUCTIONS:

- AvailabilityTool:
  Use for queries like "free beds", "bed count", "capacity of WardA"

- AssignmentTool:
  Use for commands like "assign patient", "admit John", "place Alice in WardB"

- DischargeTool:
  Use for commands like "discharge", "send home", "remove patient"

- TransferTool:
  Use for moving patients between wards

- AnalyticsTool:
  Use for summaries like "ward usage", "occupancy rate", "how many beds are free"

🧠 EXAMPLES YOU CAN HANDLE:
- "Can Alice be moved to another ward?"
- "Which ward has the most space?"
- "Admit patient P103 to Ward A"
- "Discharge Bob"
- "Transfer Charlie from Ward A to Ward B"
- "Show occupancy analytics"

Always try to:
- Confirm patient and ward names clearly
- Ask clarifying questions when input is ambiguous
- Default to safest or most available ward if no preference is given
- Respond in a friendly and professional manner
            """,
            tools=[
                AvailabilityTool(name="check_availability", description="Check availability of beds in wards"),
                AssignmentTool(name="assign_patient", description="Assign a patient to a ward"),
                DischargeTool(name="discharge_patient", description="Discharge a patient from the ward"),
                TransferTool(name="transfer_patient", description="Transfer a patient from one ward to another"),
                AnalyticsTool(name="ward_analytics", description="View ward occupancy and usage analytics")
            ]
        )

    def get_agent(self):
        return self.root_agent

    def get_database(self):
        return self.hospital_db

# Instantiate the AI system
ward_system = WardManagementSystem()

# Export root agent and database
root_agent = ward_system.get_agent()
hospital_db_instance = ward_system.get_database()

# Entry point for testing
async def main():
    print(" Enhanced Ward Management AI Agent Initialized")
    print(f"Loaded wards: {list(hospital_db_instance.wards.keys())}")
    print(f" Total patients: {len(hospital_db_instance.patients)}")
    print(" Ready to process natural language queries related to ward operations!")

if __name__ == "__main__":
    asyncio.run(main())
