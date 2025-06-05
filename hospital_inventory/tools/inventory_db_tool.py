# =========================================
# tools/inventory_db_tool.py
# =========================================
# Defines InventoryDBTool, which encapsulates all database-like
# interactions for hospital inventory: fetching current stock,
# updating quantities, etc.
# =========================================

from adk.tools import BaseTool
from datetime import datetime
from typing import List, Dict, Any

class InventoryDBTool(BaseTool):
    """
    InventoryDBTool
    ----------------
    A mock tool to simulate fetching and updating hospital inventory.
    In a production setting, you would replace the in-memory list
    with actual database queries (e.g., SQLAlchemy, MongoClient, etc.).
    """

    name = "inventory_db_tool"
    description = (
        "Tool to fetch and update hospital inventory. "
        "Provide methods for getting current stock, updating quantities, and listing items."
    )

    def __init__(self):
        super().__init__()
        # For demonstration purposes, we'll store inventory in-memory.
        # Each item is a dict with:
        #   - item_id:       Unique identifier (string)
        #   - name:          Item name (string)
        #   - quantity:      Current stock quantity (int)
        #   - reorder_threshold: If quantity < threshold, we need to reorder (int)
        #   - usage_history: List of past usage numbers (List[int]) for forecasting
        #   - expiry_date:   Expiration date as datetime
        self._inventory: List[Dict[str, Any]] = [
            {
                "item_id": "med_001",
                "name": "Paracetamol (500 mg)",
                "quantity": 20,
                "reorder_threshold": 30,
                "usage_history": [15, 18, 22, 20],  # past 4 weeks
                "expiry_date": datetime(2025, 8, 15),
            },
            {
                "item_id": "equip_002",
                "name": "Disposable Syringe (5 mL)",
                "quantity": 50,
                "reorder_threshold": 40,
                "usage_history": [45, 50, 48, 52],
                "expiry_date": datetime(2027, 12, 31),
            },
            # Add more items as needed...
        ]

    def get_stock(self) -> List[Dict[str, Any]]:
        """
        get_stock()
        -----------
        Returns the entire inventory list (in real usage, query a database).
        """
        # In production, replace this with a real DB fetch.
        return self._inventory

    def get_item_by_id(self, item_id: str) -> Dict[str, Any]:
        """
        get_item_by_id(item_id: str) -> Dict
        -------------------------------------
        Return the inventory record for a given item_id. Raises KeyError if not found.
        """
        for item in self._inventory:
            if item["item_id"] == item_id:
                return item
        raise KeyError(f"Item with ID '{item_id}' not found in inventory.")

    def update_stock(self, item_id: str, new_quantity: int) -> bool:
        """
        update_stock(item_id: str, new_quantity: int) -> bool
        -----------------------------------------------------
        Update the 'quantity' field for a given item_id.
        Returns True if successful, False otherwise.
        """
        try:
            item = self.get_item_by_id(item_id)
            item["quantity"] = new_quantity
            return True
        except KeyError:
            return False

    def record_usage(self, item_id: str, used_amount: int) -> bool:
        """
        record_usage(item_id: str, used_amount: int) -> bool
        ---------------------------------------------------
        Subtracts 'used_amount' from current quantity and
        appends used_amount to usage_history. Returns True if successful.
        """
        try:
            item = self.get_item_by_id(item_id)
            item["quantity"] -= used_amount
            item["usage_history"].append(used_amount)
            return True
        except KeyError:
            return False

    def list_low_stock(self) -> List[Dict[str, Any]]:
        """
        list_low_stock() -> List[Dict]
        ------------------------------
        Returns a list of items whose quantity is below reorder_threshold.
        """
        low_stock_items = []
        for item in self._inventory:
            if item["quantity"] < item["reorder_threshold"]:
                low_stock_items.append(item)
        return low_stock_items

    def list_expiring_soon(self, within_days: int = 30) -> List[Dict[str, Any]]:
        """
        list_expiring_soon(within_days: int) -> List[Dict]
        --------------------------------------------------
        Returns items whose expiry_date is within the next 'within_days' days.
        """
        upcoming = []
        cutoff = datetime.now() + timedelta(days=within_days)
        for item in self._inventory:
            if item["expiry_date"] <= cutoff:
                upcoming.append(item)
        return upcoming
