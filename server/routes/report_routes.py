from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends

from auth import get_current_user
from models import DietPlan, Patient, User

router = APIRouter(prefix="/api/reports", tags=["reports"])


def _iso(value):
    """Normalise stored datetimes (including legacy strings) to ISO-8601."""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value).isoformat()
        except ValueError:
            return value
    return value


@router.get("/weekly")
async def get_weekly_report(
    current_user: User = Depends(get_current_user),
):
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    user_id_str = str(current_user.id)

    # New patients in last 7 days
    new_patients_count = await Patient.find(
        Patient.user_id == user_id_str,
        Patient.created_at >= seven_days_ago,
    ).count()

    # Diet plans in last 7 days
    new_plans_count = await DietPlan.find(
        DietPlan.user_id == user_id_str,
        DietPlan.created_at >= seven_days_ago,
    ).count()

    # Patient distribution by Vikriti
    pipeline = [
        {"$match": {"user_id": user_id_str}},
        {"$group": {"_id": "$vikriti", "count": {"$sum": 1}}}
    ]
    vikriti_dist = await Patient.aggregate(pipeline).to_list()
    vikriti_stats = {item["_id"]: item["count"] for item in vikriti_dist if item["_id"]}

    # Recent patients
    recent_patients = (
        await Patient.find(Patient.user_id == user_id_str)
        .sort([("created_at", -1)])
        .limit(5)
        .to_list()
    )

    return {
        "stats": {
            "new_patients": new_patients_count,
            "new_plans": new_plans_count,
            "vikriti_breakdown": vikriti_stats,
        },
        "recent_patients": [
            {
                "id": str(p.id),
                "name": p.name,
                "vikriti": p.vikriti,
                "created_at": _iso(p.created_at)
            }
            for p in recent_patients
        ],
    }
