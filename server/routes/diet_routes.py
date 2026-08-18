from fastapi import APIRouter, Depends, HTTPException

import schemas
from auth import get_current_user
from engine.ayur_logic import generate_plan
from engine.conflict_checker import check_conflict
from models import DietPlan, DietTemplate, Food, Patient, User, dump_doc, to_object_id

router = APIRouter(tags=["diet"])


def _format_plan(plan: dict) -> dict:
    plan["id"] = str(plan["_id"])
    for idx, item in enumerate(plan.get("items", [])):
        item["id"] = str(item.get("_id") or idx)
        if "food" in item and "_id" in item["food"]:
            item["food"]["id"] = str(item["food"]["_id"])
    return plan


@router.get("/api/templates", response_model=list[schemas.TemplateOut])
async def list_templates(
    current_user: User = Depends(get_current_user),
):
    _ = current_user
    templates = await DietTemplate.find_all().sort([("_id", 1)]).to_list()
    return [dump_doc(t) for t in templates]


@router.get("/api/diet-plans", response_model=list[schemas.DietPlanOut])
async def list_diet_plans(
    current_user: User = Depends(get_current_user),
):
    plans = (
        await DietPlan.find(DietPlan.user_id == str(current_user.id))
        .sort([("created_at", -1)])
        .to_list()
    )
    return [_format_plan(dump_doc(p)) for p in plans]


@router.post("/api/diet-plans/generate", response_model=schemas.DietPlanOut)
async def create_plan(
    payload: schemas.DietPlanGenerateRequest,
    current_user: User = Depends(get_current_user),
):
    patient_oid = to_object_id(payload.patient_id)
    patient = (
        await Patient.find_one(Patient.id == patient_oid, Patient.user_id == str(current_user.id))
        if patient_oid
        else None
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    template_oid = to_object_id(payload.template_id)
    template = await DietTemplate.find_one(DietTemplate.id == template_oid) if template_oid else None
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    plan = await generate_plan(dump_doc(patient), str(current_user.id), dump_doc(template))
    return _format_plan(plan)


@router.get("/api/diet-plans/{plan_id}", response_model=schemas.DietPlanOut)
async def get_plan(
    plan_id: str,
    current_user: User = Depends(get_current_user),
):
    oid = to_object_id(plan_id)
    plan = (
        await DietPlan.find_one(DietPlan.id == oid, DietPlan.user_id == str(current_user.id))
        if oid
        else None
    )
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return _format_plan(dump_doc(plan))


@router.get("/api/public/plan/{plan_id}", response_model=schemas.DietPlanOut)
async def get_public_plan(plan_id: str):
    oid = to_object_id(plan_id)
    plan = await DietPlan.find_one(DietPlan.id == oid) if oid else None
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return _format_plan(dump_doc(plan))


@router.get("/api/diet-plans/patient/{patient_id}", response_model=list[schemas.DietPlanOut])
async def list_plans_for_patient(
    patient_id: str,
    current_user: User = Depends(get_current_user),
):
    plans = (
        await DietPlan.find(
            DietPlan.patient_id == patient_id,
            DietPlan.user_id == str(current_user.id),
        )
        .sort([("_id", -1)])
        .to_list()
    )
    return [_format_plan(dump_doc(p)) for p in plans]


@router.put("/api/diet-plans/{plan_id}", response_model=schemas.DietPlanOut)
async def update_plan(
    plan_id: str,
    payload: schemas.DietPlanUpdate,
    current_user: User = Depends(get_current_user),
):
    oid = to_object_id(plan_id)
    plan = (
        await DietPlan.find_one(DietPlan.id == oid, DietPlan.user_id == str(current_user.id))
        if oid
        else None
    )
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    if payload.notes is not None:
        plan.notes = payload.notes
    if payload.target_calories is not None:
        plan.target_calories = payload.target_calories
    if payload.target_protein is not None:
        plan.target_protein = payload.target_protein
    if payload.target_carbs is not None:
        plan.target_carbs = payload.target_carbs
    if payload.target_fat is not None:
        plan.target_fat = payload.target_fat

    # Update embedded items
    if payload.items:
        patient_oid = to_object_id(plan.patient_id)
        patient = await Patient.find_one(Patient.id == patient_oid) if patient_oid else None
        patient_dict = dump_doc(patient) if patient else None

        for item_update in payload.items:
            for idx, item in enumerate(plan.items):
                item_id = item.item_id or str(idx)
                if item_id != str(item_update.id):
                    continue
                food_oid = to_object_id(item_update.food_id)
                food = await Food.find_one(Food.id == food_oid) if food_oid else None
                if not food:
                    raise HTTPException(status_code=404, detail="Food not found")
                factor = item_update.portion_g / 100.0
                food_dict = dump_doc(food)
                item.food_id = str(food.id)
                item.food = food_dict
                item.portion_g = item_update.portion_g
                item.calories = round(food.calories * factor, 2)
                item.protein = round(food.protein_g * factor, 2)
                item.carbs = round(food.carbs_g * factor, 2)
                item.fat = round(food.fat_g * factor, 2)
                if patient_dict:
                    is_conflict, reason = check_conflict(food_dict, patient_dict)
                    item.is_conflict = is_conflict
                    item.reasoning = (
                        reason or f"{food.name} selected for "
                        f"{item.meal_slot} (Day {item.day_of_week})."
                    )
                break

        day_count = len({i.day_of_week for i in plan.items}) or 1
        plan.total_calories = round(sum(i.calories for i in plan.items) / day_count, 2)
        plan.total_protein = round(sum(i.protein for i in plan.items) / day_count, 2)
        plan.total_carbs = round(sum(i.carbs for i in plan.items) / day_count, 2)
        plan.total_fat = round(sum(i.fat for i in plan.items) / day_count, 2)

    await plan.save()
    return _format_plan(dump_doc(plan))
