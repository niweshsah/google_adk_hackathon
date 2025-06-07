from google.adk.tools import BaseTool
from models import hospital_db

class AssignmentTool(BaseTool):
    def __init__(self, *, name: str, description: str):
        super().__init__(name=name, description=description)

    def run(self, input_data: dict) -> dict:
        patient_id = input_data.get("patient_id")
        ward_name = input_data.get("ward_name")

        if not patient_id or not ward_name:
            return {"status": "error", "message": "Missing patient_id or ward_name"}

        patient = hospital_db.patients.get(patient_id)
        ward = hospital_db.wards.get(ward_name)

        if not patient:
            return {"status": "error", "message": f"Patient {patient_id} not found"}
        if not ward:
            return {"status": "error", "message": f"Ward {ward_name} not found"}

        success = ward.assign_patient(patient)
        return {"status": "success" if success else "error", "message": f"Patient {patient_id} assigned to {ward_name}" if success else "Ward full or already assigned"}
