from google.adk.tools import BaseTool
from models import hospital_db

class TransferTool(BaseTool):
    def __init__(self, *, name: str, description: str):
        super().__init__(name=name, description=description)

    def run(self, input_data: dict) -> dict:
        patient_id = input_data.get("patient_id")
        from_ward_name = input_data.get("from_ward")
        to_ward_name = input_data.get("to_ward")

        if not patient_id or not from_ward_name or not to_ward_name:
            return {"status": "error", "message": "Missing patient_id, from_ward, or to_ward"}

        from_ward = hospital_db.wards.get(from_ward_name)
        to_ward = hospital_db.wards.get(to_ward_name)
        patient = hospital_db.patients.get(patient_id)

        if not all([from_ward, to_ward, patient]):
            return {"status": "error", "message": "Invalid ward or patient"}

        if not from_ward.has_patient(patient_id):
            return {"status": "error", "message": f"Patient {patient_id} not in {from_ward_name}"}

        if to_ward.is_full():
            return {"status": "error", "message": f"Target ward {to_ward_name} is full"}

        from_ward.discharge_patient(patient_id)
        to_ward.assign_patient(patient)

        return {"status": "success", "message": f"Transferred {patient_id} from {from_ward_name} to {to_ward_name}"}
