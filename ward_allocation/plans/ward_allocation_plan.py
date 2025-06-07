# plans/ward_allocation_plan.py

from ..tools.availability_tool import WardAvailabilityTool
from ..tools.assignment_tool import AssignmentTool
from ..tools.discharge_tool import DischargeTool
from ..tools.transfer_tool import TransferTool
from ..tools.analytics_tool import WardAnalyticsTool

class WardAllocationPlan:
    """
    This plan coordinates all ward-level decisions:
    - Assigning patients to wards
    - Transferring patients between wards
    - Discharging patients
    - Monitoring occupancy and availability
    """

    def __init__(self):
        self.availability_tool = WardAvailabilityTool()
        self.assignment_tool = AssignmentTool()
        self.discharge_tool = DischargeTool()
        self.transfer_tool = TransferTool()
        self.analytics_tool = WardAnalyticsTool()

    def run_full_allocation_cycle(self):
        """
        Executes a full cycle of ward management:
        1. Check availability
        2. Assign waiting patients
        3. Generate occupancy report
        """
        print("🔍 Checking current availability...")
        availability = self.availability_tool.get_available_beds()
        print("✅ Availability:", availability)

        print("\n📊 Generating occupancy analytics...")
        analytics = self.analytics_tool.get_occupancy_report()
        for ward, data in analytics.items():
            print(f"- {ward}: {data['occupancy_percent']}% occupied ({data['occupied_beds']}/{data['total_beds']})")

        return {
            "availability": availability,
            "analytics": analytics
        }

    def assign_patient(self, patient_id, preferred_ward=None):
        """
        Assign a patient to a ward.
        """
        return self.assignment_tool.assign_patient_to_bed(patient_id, preferred_ward)

    def discharge_patient(self, patient_id):
        """
        Discharge a patient from their ward.
        """
        return self.discharge_tool.discharge_patient(patient_id)

    def transfer_patient(self, patient_id, from_ward, to_ward):
        """
        Transfer a patient to another ward.
        """
        return self.transfer_tool.transfer_patient(patient_id, from_ward, to_ward)

    def get_report(self):
        """
        Get availability + analytics in one go.
        """
        return self.run_full_allocation_cycle()
