# agent.py

from vertexai.preview.agentbuilder import create_tool, create_agent
from tools.inventory_db_tool import InventoryDBTool
from plans.reorder_plan import ReorderPlan

# Step 1: Register tool with ADK
InventoryDBToolTool = create_tool(InventoryDBTool)

# Step 2: Create the ADK Agent with metadata
agent = create_agent(
    name="InventoryAgent",
    description=(
        "ADK agent for hospital inventory management: monitors stock levels, "
        "forecasts upcoming demand, and suggests reorder quantities."
    ),
    tools=[InventoryDBToolTool],
    plans=[ReorderPlan],
)

# Step 3: Run the agent in interactive mode
if __name__ == "__main__":
    agent.run()
