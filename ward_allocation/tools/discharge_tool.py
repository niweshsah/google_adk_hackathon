from google.adk.tools import BaseTool
from models import hospital_db

class DischargeTool(BaseTool):
    def __init__(self, *, name: str, description: str):
        super().__init__(name=name, description=description)

    def run(self, input_data: dict) -> dict:
        patient_id = input_data.get("patient_id")

        if not patient_id:
            return {"status": "error", "message": "Missing patient_id"}

        patient = hospital_db.patients.get(patient_id)
        if not patient:
            return {"status": "error", "message": f"Patient {patient_id} not found"}

        for ward in hospital_db.wards.values():
            if ward.has_patient(patient_id):
                ward.discharge_patient(patient_id)
                return {"status": "success", "message": f"Patient {patient_id} discharged from {ward.name}"}

        return {"status": "error", "message": f"Patient {patient_id} is not assigned to any ward"}
