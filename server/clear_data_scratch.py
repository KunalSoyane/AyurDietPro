"""Clear all patient and diet-plan data (users, foods and templates are kept).

Usage:
    python clear_data_scratch.py
"""

import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import close_db, init_db
from models import DietPlan, Patient


async def clear_data():
    await init_db()

    plans_result = await DietPlan.find_all().delete()
    print(f"Deleted {plans_result.deleted_count} diet plans.")

    patients_result = await Patient.find_all().delete()
    print(f"Deleted {patients_result.deleted_count} patients.")

    print("Successfully reset all patient and chart counts to zero.")

    await close_db()


if __name__ == "__main__":
    asyncio.run(clear_data())
