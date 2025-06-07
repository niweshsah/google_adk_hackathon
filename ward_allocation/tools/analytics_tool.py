from google.adk.tools import BaseTool
from models import hospital_db

class AnalyticsTool(BaseTool):
    def __init__(self, *, name: str, description: str):
        super().__init__(name=name, description=description)

    def run(self, input_data: dict = None) -> dict:
        usage = {}
        total_capacity = 0
        total_occupied = 0

        for ward_name, ward in hospital_db.wards.items():
            total_beds = ward.capacity
            occupied = ward.occupancy()
            usage[ward_name] = {
                "total_beds": total_beds,
                "occupied": occupied,
                "occupancy_percent": round((occupied / total_beds) * 100, 2) if total_beds else 0
            }
            total_capacity += total_beds
            total_occupied += occupied

        usage["overall"] = {
            "total_beds": total_capacity,
            "total_occupied": total_occupied,
            "overall_occupancy_percent": round((total_occupied / total_capacity) * 100, 2) if total_capacity else 0
        }

        return usage
