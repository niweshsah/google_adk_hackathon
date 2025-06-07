from google.adk.tools import BaseTool
from models import hospital_db

class AvailabilityTool(BaseTool):
    def __init__(self, *, name: str, description: str):
        super().__init__(name=name, description=description)

    def run(self, input_data: dict = None) -> dict:
        report = {}
        for ward_name, ward in hospital_db.wards.items():
            total_beds = ward.capacity
            occupied = ward.occupancy()
            report[ward_name] = {
                "total_beds": total_beds,
                "occupied_beds": occupied,
                "occupancy_percent": round((occupied / total_beds) * 100, 2) if total_beds else 0
            }
        return report
