# # =========================================
# # plans/reorder_plan.py
# # =========================================
# # Defines ReorderPlan, which:
# # 1. Fetches current inventory via InventoryDBTool
# # 2. For each item, uses LinearRegression to forecast next-week usage
# # 3. Determines if projected remaining stock < reorder_threshold
# # 4. Builds a list of reorder suggestions
# # =========================================

# from adk.planner import BasePlan
# from typing import Dict, Any
# from sklearn.linear_model import LinearRegression
# import numpy as np

# class ReorderPlan(BasePlan):
#     """
#     ReorderPlan
#     -----------
#     A plan that:
#     1. Retrieves inventory data from InventoryDBTool.
#     2. Builds a linear regression model on historical usage.
#     3. Predicts next-week usage.
#     4. Compares projected remaining stock vs. reorder_threshold.
#     5. Returns a structured list of suggestions.
#     """

#     name = "ReorderPlan"
#     description = (
#         "Forecasts demand and suggests reorder quantities for items "
#         "that will fall below their reorder threshold."
#     )

#     def run(self, tools: Dict[str, Any], memory: Any, **kwargs) -> Dict[str, Any]:
#         """
#         run(...)
#         -------
#         - tools: Dictionary of instantiated tools. We expect 'inventory_db_tool'.
#         - memory: ADK memory object (unused here, but could store past forecasts).
#         - **kwargs: Additional keyword args (ignored for now).
#         Returns a dict with a single key 'reorder_suggestions' mapping to a list.
#         """
#         # 1. Retrieve the InventoryDBTool instance
#         db_tool = tools["inventory_db_tool"]

#         # 2. Fetch the full inventory
#         inventory_list = db_tool.get_stock()

#         suggestions = []

#         # 3. Loop over each item and forecast next-week usage
#         for item in inventory_list:
#             usage_history = item.get("usage_history", [])
#             current_qty = item.get("quantity", 0)
#             threshold = item.get("reorder_threshold", 0)

#             # Skip items with insufficient history (need at least two data points)
#             if len(usage_history) < 2:
#                 continue

#             # Prepare data for linear regression
#             # X = 0,1,2,... for each week index
#             X = np.arange(len(usage_history)).reshape(-1, 1)  # shape: (n_samples, 1)
#             y = np.array(usage_history)                        # shape: (n_samples,)

#             # Train a simple LinearRegression model
#             model = LinearRegression()
#             model.fit(X, y)

#             # Predict usage for the next index (len(usage_history))
#             next_index = np.array([[len(usage_history)]])  # shape: (1, 1)
#             predicted_usage = model.predict(next_index)[0]

#             # Round predicted usage to nearest integer (no negative usage)
#             predicted_usage = max(int(round(predicted_usage)), 0)

#             # Compute projected quantity after next-week usage
#             projected_remaining = current_qty - predicted_usage

#             # If projected remaining < threshold, we need to reorder
#             if projected_remaining < threshold:
#                 reorder_amount = (threshold + predicted_usage) - current_qty
#                 # Ensure reorder_amount is positive
#                 reorder_amount = max(reorder_amount, 0)

#                 suggestions.append({
#                     "item_id": item["item_id"],
#                     "name": item["name"],
#                     "current_quantity": current_qty,
#                     "predicted_next_week_usage": predicted_usage,
#                     "projected_remaining": projected_remaining,
#                     "reorder_threshold": threshold,
#                     "suggested_reorder_quantity": reorder_amount
#                 })

#         # 4. Return all suggestions in a structured dictionary
#         return {"reorder_suggestions": suggestions}

































import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from prophet import Prophet
from adk.planner import BasePlan
from typing import Dict, Any, List


class ReorderPlan(BasePlan):
    name = "ReorderPlan"
    description = (
        "Forecasts demand using Prophet (with Linear Regression fallback) and returns reorder suggestions. "
        "Adds criticality scoring, demand classification, and depletion monitoring."
    )

    def run(self, tools: Dict[str, Any], memory: Any, **kwargs) -> Dict[str, Any]:
        db_tool = tools.get("inventory_db_tool")
        if not db_tool:
            raise ValueError("Missing required tool: inventory_db_tool")

        inventory_list = db_tool.get_stock()
        forecast_weeks = kwargs.get("forecast_weeks", 1)
        min_required_history = kwargs.get("min_history", 7)

        reorder_suggestions: List[Dict[str, Any]] = []

        for item in inventory_list:
            try:
                item_id = item["item_id"]
                item_name = item.get("name", "Unnamed Item")
                current_qty = int(item.get("quantity", 0))
                threshold = int(item.get("reorder_threshold", 0))
                usage_history = item.get("usage_history", [])

                usage_series = pd.Series(usage_history).dropna()
                usage_series = usage_series[usage_series >= 0]

                if len(usage_series) < min_required_history:
                    self._log(f"Skipping '{item_name}' (ID: {item_id}) — insufficient usage history.", memory)
                    continue

                # Create historical time series
                today = pd.Timestamp.today().normalize()
                dates = [today - pd.Timedelta(weeks=i) for i in range(len(usage_series)-1, -1, -1)]
                df = pd.DataFrame({"ds": dates, "y": usage_series.values})

                # Demand classification
                total_usage = usage_series.sum()
                if total_usage > 100:
                    demand_class = "fast-moving"
                elif total_usage > 30:
                    demand_class = "medium"
                else:
                    demand_class = "slow-moving"

                # Depletion rate (last 3 weeks avg)
                recent_avg = usage_series.tail(3).mean()
                depletion_flag = recent_avg > usage_series.mean() * 1.5  # e.g. 50% spike

                # Criticality scoring (simplified — in real cases, link to item metadata)
                if "syringe" in item_name.lower() or "emergency" in item_name.lower():
                    criticality = "high"
                elif demand_class == "fast-moving":
                    criticality = "medium"
                else:
                    criticality = "low"

                # Forecasting with Prophet
                try:
                    model = Prophet(weekly_seasonality=True, daily_seasonality=False, yearly_seasonality=False)
                    model.fit(df)
                    future = model.make_future_dataframe(periods=forecast_weeks, freq="W")
                    forecast = model.predict(future)
                    predicted_usage = forecast["yhat"].iloc[-forecast_weeks:].mean()
                except Exception as e:
                    self._log(f"Prophet failed for {item_name}. Falling back to Linear Regression. {e}", memory)
                    X = np.arange(len(usage_series)).reshape(-1, 1)
                    y = usage_series.values
                    linreg = LinearRegression().fit(X, y)
                    X_pred = np.arange(len(usage_series), len(usage_series) + forecast_weeks).reshape(-1, 1)
                    predicted_usage = linreg.predict(X_pred).mean()

                predicted_usage = max(int(round(predicted_usage)), 0)
                projected_remaining = current_qty - predicted_usage

                if projected_remaining < threshold:
                    reorder_qty = (threshold + predicted_usage) - current_qty
                    reorder_qty = max(reorder_qty, 0)

                    reorder_suggestions.append({
                        "item_id": item_id,
                        "name": item_name,
                        "current_quantity": current_qty,
                        "predicted_next_week_usage": predicted_usage,
                        "projected_remaining": projected_remaining,
                        "reorder_threshold": threshold,
                        "suggested_reorder_quantity": reorder_qty,
                        "demand_classification": demand_class,
                        "criticality": criticality,
                        "depletion_rate_spike": depletion_flag,
                        "confidence": round(float(predicted_usage / (usage_series.mean() + 1e-5)), 2)
                    })

            except Exception as e:
                self._log(f"Error processing item {item.get('name', '')} (ID: {item.get('item_id', '')}): {e}", memory)
                continue

        return {"reorder_suggestions": reorder_suggestions}

    def _log(self, message: str, memory: Any = None):
        print(f"[ReorderPlan] {message}")
        if memory and hasattr(memory, "add_log"):
            memory.add_log("ReorderPlan", message)
