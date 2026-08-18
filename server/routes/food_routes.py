from fastapi import APIRouter, Depends, HTTPException
import re

import schemas
from auth import get_current_user
from models import Food, User, dump_doc, to_object_id

router = APIRouter(prefix="/api/foods", tags=["foods"])


@router.get("", response_model=list[schemas.FoodOut])
async def list_foods(
    q: str | None = None,
    category: str | None = None,
    vegetarian: bool | None = None,
    vikriti: str | None = None,
    current_user: User = Depends(get_current_user),
):
    _ = current_user
    filter_query: dict = {}

    if q:
        filter_query["name"] = {"$regex": re.escape(q), "$options": "i"}
    if category:
        filter_query["category"] = category
    if vegetarian is not None:
        filter_query["is_vegetarian"] = vegetarian

    if vikriti:
        v = vikriti.lower()
        if v == "vata":
            filter_query["vata_effect"] = {"$lte": 0}
        elif v == "pitta":
            filter_query["pitta_effect"] = {"$lte": 0}
        elif v == "kapha":
            filter_query["kapha_effect"] = {"$lte": 0}

    foods = await Food.find(filter_query).sort("name").limit(200).to_list()
    return [dump_doc(f) for f in foods]


@router.get("/categories", response_model=list[str])
async def list_categories(
    current_user: User = Depends(get_current_user),
):
    _ = current_user
    categories = await Food.get_motor_collection().distinct("category")
    return sorted(categories)


@router.get("/{food_id}", response_model=schemas.FoodOut)
async def get_food(
    food_id: str,
    current_user: User = Depends(get_current_user),
):
    _ = current_user
    oid = to_object_id(food_id)
    food = await Food.find_one(Food.id == oid) if oid else None
    if not food:
        raise HTTPException(status_code=404, detail="Food not found")
    return dump_doc(food)
