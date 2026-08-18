"""
Admin Routes — accessible only to users with role='admin'.

Endpoints:
  GET    /api/admin/stats              – System-wide statistics
  GET    /api/admin/users              – List all users (doctors + admins)
  POST   /api/admin/users              – Create a new user
  PUT    /api/admin/users/{id}         – Update user name / role
  DELETE /api/admin/users/{id}         – Delete a user
  GET    /api/admin/patients           – All patients across all doctors
  DELETE /api/admin/patients/{id}      – Delete any patient
  GET    /api/admin/foods              – All foods (same as public but no limit)
  POST   /api/admin/foods              – Add a new food
  PUT    /api/admin/foods/{id}         – Edit a food
  DELETE /api/admin/foods/{id}         – Delete a food
  GET    /api/admin/diet-plans         – All diet plans across all users
  DELETE /api/admin/diet-plans/{id}    – Delete any diet plan
"""

from datetime import datetime, timedelta, timezone

from beanie.operators import In
from fastapi import APIRouter, Depends, HTTPException

from auth import get_admin_user, get_password_hash
from models import DietPlan, Food, Patient, User, dump_doc, to_object_id

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ─── helpers ────────────────────────────────────────────────────────────────

def _public(doc_dict: dict) -> dict:
    """Expose the document id as `id` for JSON responses."""
    doc_dict["id"] = str(doc_dict.pop("_id", ""))
    return doc_dict


def _as_float(value, field: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail=f"{field} must be a number")


def _as_int(value, field: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail=f"{field} must be an integer")


# ─── Stats ──────────────────────────────────────────────────────────────────

@router.get("/stats")
async def get_stats(
    _admin: User = Depends(get_admin_user),
):
    """Return high-level platform statistics."""
    total_users    = await User.find_all().count()
    total_doctors  = await User.find(User.role == "doctor").count()
    total_admins   = await User.find(User.role == "admin").count()
    total_patients = await Patient.find_all().count()
    total_plans    = await DietPlan.find_all().count()
    total_foods    = await Food.find_all().count()

    # Patients per vikriti
    vikriti_pipeline = [
        {"$group": {"_id": "$vikriti", "count": {"$sum": 1}}}
    ]
    vikriti_rows = await Patient.aggregate(vikriti_pipeline).to_list()
    vikriti_breakdown = {
        item["_id"]: item["count"] for item in vikriti_rows if item["_id"]
    }

    # Plans and patients in last 7 days
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_plans = await DietPlan.find(
        DietPlan.created_at >= seven_days_ago
    ).count()
    recent_patients = await Patient.find(
        Patient.created_at >= seven_days_ago
    ).count()

    return {
        "users": {
            "total": total_users,
            "doctors": total_doctors,
            "admins": total_admins,
        },
        "patients": {
            "total": total_patients,
            "last_7_days": recent_patients,
            "vikriti_breakdown": vikriti_breakdown,
        },
        "diet_plans": {
            "total": total_plans,
            "last_7_days": recent_plans,
        },
        "foods": {
            "total": total_foods,
        },
    }


# ─── User Management ────────────────────────────────────────────────────────

@router.get("/users")
async def list_users(
    _admin: User = Depends(get_admin_user),
):
    users = await User.find_all().sort([("created_at", -1)]).to_list()
    result = []
    for user in users:
        data = dump_doc(user)
        data.pop("password_hash", None)
        result.append(_public(data))
    return result


@router.post("/users", status_code=201)
async def create_user(
    payload: dict,
    _admin: User = Depends(get_admin_user),
):
    """Create a doctor or admin account."""
    name = payload.get("name")
    email_raw = payload.get("email")
    password = payload.get("password")
    if not isinstance(name, str) or not name.strip():
        raise HTTPException(status_code=422, detail="name must be a non-empty string")
    if not isinstance(email_raw, str) or not email_raw.strip():
        raise HTTPException(status_code=422, detail="email must be a non-empty string")
    if not isinstance(password, str) or not password:
        raise HTTPException(status_code=422, detail="password must be a non-empty string")

    email = email_raw.lower().strip()

    if await User.find_one(User.email == email):
        raise HTTPException(status_code=409, detail="Email already registered")

    role = payload.get("role", "doctor")
    if role not in ("doctor", "admin"):
        raise HTTPException(status_code=422, detail="role must be 'doctor' or 'admin'")

    user = User(
        name=name.strip(),
        email=email,
        password_hash=get_password_hash(password),
        role=role,
        created_at=datetime.now(timezone.utc),
    )
    await user.insert()
    user_doc = dump_doc(user)
    user_doc.pop("password_hash", None)
    return _public(user_doc)


@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    payload: dict,
    admin: User = Depends(get_admin_user),
):
    """Update a user's name or role. Cannot demote yourself."""
    if (
        user_id == str(admin.id)
        and "role" in payload
        and payload["role"] != "admin"
    ):
        raise HTTPException(status_code=400, detail="Cannot demote your own admin account")

    update = {}
    if "name" in payload:
        if not isinstance(payload["name"], str) or not payload["name"].strip():
            raise HTTPException(status_code=422, detail="name must be a non-empty string")
        update["name"] = payload["name"].strip()
    if "role" in payload:
        if payload["role"] not in ("doctor", "admin"):
            raise HTTPException(status_code=422, detail="role must be 'doctor' or 'admin'")
        update["role"] = payload["role"]
    if "password" in payload and payload["password"]:
        if not isinstance(payload["password"], str):
            raise HTTPException(status_code=422, detail="password must be a string")
        update["password_hash"] = get_password_hash(payload["password"])

    if not update:
        raise HTTPException(status_code=422, detail="No valid fields to update")

    oid = to_object_id(user_id)
    user = await User.find_one(User.id == oid) if oid else None
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    for field, value in update.items():
        setattr(user, field, value)
    await user.save()

    user_doc = dump_doc(user)
    user_doc.pop("password_hash", None)
    return _public(user_doc)


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    admin: User = Depends(get_admin_user),
):
    """Delete a user. Cannot delete yourself. Cascades their patients and plans."""
    if user_id == str(admin.id):
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    oid = to_object_id(user_id)
    user = await User.find_one(User.id == oid) if oid else None
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await user.delete()

    patient_ids = [
        str(p.id) for p in await Patient.find(Patient.user_id == user_id).to_list()
    ]
    if patient_ids:
        await DietPlan.find(In(DietPlan.patient_id, patient_ids)).delete()
    await Patient.find(Patient.user_id == user_id).delete()
    await DietPlan.find(DietPlan.user_id == user_id).delete()
    return {"success": True, "deleted_id": user_id}


# ─── Patient Management ─────────────────────────────────────────────────────

@router.get("/patients")
async def list_all_patients(
    _admin: User = Depends(get_admin_user),
):
    """Return all patients across all doctors."""
    patients = await Patient.find_all().sort([("created_at", -1)]).to_list()
    return [_public(dump_doc(p)) for p in patients]


@router.delete("/patients/{patient_id}")
async def delete_patient(
    patient_id: str,
    _admin: User = Depends(get_admin_user),
):
    oid = to_object_id(patient_id)
    patient = await Patient.find_one(Patient.id == oid) if oid else None
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    await patient.delete()
    # Also remove their plans
    await DietPlan.find(DietPlan.patient_id == patient_id).delete()
    return {"success": True}


# ─── Food Management ────────────────────────────────────────────────────────

@router.get("/foods")
async def list_all_foods(
    _admin: User = Depends(get_admin_user),
):
    foods = await Food.find_all().sort("name").to_list()
    return [_public(dump_doc(f)) for f in foods]


@router.post("/foods", status_code=201)
async def create_food(
    payload: dict,
    _admin: User = Depends(get_admin_user),
):
    """Add a new food to the database."""
    if not payload.get("name") or not payload.get("category"):
        raise HTTPException(status_code=422, detail="name and category are required")
    if not isinstance(payload["name"], str) or not isinstance(payload["category"], str):
        raise HTTPException(status_code=422, detail="name and category must be strings")

    if await Food.find_one(Food.name == payload["name"]):
        raise HTTPException(status_code=409, detail="Food with this name already exists")

    food = Food(
        name=payload["name"],
        name_hindi=payload.get("name_hindi"),
        category=payload["category"],
        subcategory=payload.get("subcategory"),
        calories=_as_float(payload.get("calories", 0), "calories"),
        protein_g=_as_float(payload.get("protein_g", 0), "protein_g"),
        carbs_g=_as_float(payload.get("carbs_g", 0), "carbs_g"),
        fat_g=_as_float(payload.get("fat_g", 0), "fat_g"),
        fiber_g=_as_float(payload.get("fiber_g", 0), "fiber_g"),
        rasa=payload.get("rasa"),
        virya=payload.get("virya"),
        vipaka=payload.get("vipaka"),
        vata_effect=_as_int(payload.get("vata_effect", 0), "vata_effect"),
        pitta_effect=_as_int(payload.get("pitta_effect", 0), "pitta_effect"),
        kapha_effect=_as_int(payload.get("kapha_effect", 0), "kapha_effect"),
        is_pathya_for=payload.get("is_pathya_for", []),
        is_apathya_for=payload.get("is_apathya_for", []),
        is_vegetarian=bool(payload.get("is_vegetarian", True)),
        season_best=payload.get("season_best"),
        description=payload.get("description"),
    )
    await food.insert()
    return _public(dump_doc(food))


@router.put("/foods/{food_id}")
async def update_food(
    food_id: str,
    payload: dict,
    _admin: User = Depends(get_admin_user),
):
    """Edit any field of a food."""
    allowed_fields = {
        "name", "name_hindi", "category", "subcategory", "calories",
        "protein_g", "carbs_g", "fat_g", "fiber_g", "rasa", "virya",
        "vipaka", "vata_effect", "pitta_effect", "kapha_effect",
        "is_pathya_for", "is_apathya_for", "is_vegetarian",
        "season_best", "description",
    }
    update = {k: v for k, v in payload.items() if k in allowed_fields}
    if not update:
        raise HTTPException(status_code=422, detail="No valid fields provided")

    oid = to_object_id(food_id)
    food = await Food.find_one(Food.id == oid) if oid else None
    if not food:
        raise HTTPException(status_code=404, detail="Food not found")

    for field, value in update.items():
        setattr(food, field, value)
    await food.save()

    return _public(dump_doc(food))


@router.delete("/foods/{food_id}")
async def delete_food(
    food_id: str,
    _admin: User = Depends(get_admin_user),
):
    oid = to_object_id(food_id)
    food = await Food.find_one(Food.id == oid) if oid else None
    if not food:
        raise HTTPException(status_code=404, detail="Food not found")
    await food.delete()
    return {"success": True}


# ─── Diet Plan Management ───────────────────────────────────────────────────

@router.get("/diet-plans")
async def list_all_plans(
    _admin: User = Depends(get_admin_user),
):
    """All diet plans across all users (without embedded items for performance)."""
    plans = (
        await DietPlan.find_all()
        .sort([("created_at", -1)])
        .limit(500)
        .to_list()
    )
    result = []
    for plan in plans:
        data = dump_doc(plan)
        data.pop("items", None)
        result.append(_public(data))
    return result


@router.delete("/diet-plans/{plan_id}")
async def delete_plan(
    plan_id: str,
    _admin: User = Depends(get_admin_user),
):
    oid = to_object_id(plan_id)
    plan = await DietPlan.find_one(DietPlan.id == oid) if oid else None
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    await plan.delete()
    return {"success": True}
