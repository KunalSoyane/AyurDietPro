import random
from collections import defaultdict
from datetime import datetime, timezone
from uuid import uuid4

from engine.conflict_checker import check_conflict
from models import DietPlan, Food, dump_doc

MEAL_SPLITS = {
    "Breakfast": 0.25,
    "Lunch": 0.40,
    "Evening Snack": 0.10,
    "Dinner": 0.25,
}

# Default category order if not specified in template
DEFAULT_CATEGORY_ORDER = {
    "Breakfast": ["Grains", "Fruits", "Dairy"],
    "Lunch": ["Prepared Dishes", "Vegetables", "Lentils/Pulses", "Grains"],
    "Evening Snack": ["Fruits", "Nuts & Seeds", "Beverages"],
    "Dinner": ["Vegetables", "Lentils/Pulses", "Prepared Dishes", "Grains"],
}


def calculate_bmr(patient: dict) -> float:
    # Handle missing patient data gracefully
    weight = patient.get("weight_kg") or 70.0
    height = patient.get("height_cm") or 170.0
    age = patient.get("age") or 30
    gender = patient.get("gender")

    if gender and gender.lower() == "male":
        base = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
    else:
        base = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)

    activity_level = patient.get("activity_level", "light")
    activity_multiplier = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9,
    }.get(activity_level, 1.375)
    return max(base * activity_multiplier, 1200)


def _dosha_compatible(food: dict, vikriti: str) -> bool:
    v = vikriti.lower()
    if v == "pitta":
        return food.get("pitta_effect", 0) <= 0 and (food.get("virya") or "").lower() in {"cooling", "neutral"}
    if v == "vata":
        return food.get("vata_effect", 0) <= 0 and (food.get("virya") or "").lower() in {"warming", "neutral"}
    if v == "kapha":
        return food.get("kapha_effect", 0) <= 0 and (food.get("virya") or "").lower() in {"warming", "neutral"}
    return True


async def generate_plan(patient: dict, doctor_id: str, template: dict) -> dict:
    target_calories = calculate_bmr(patient)
    target_protein = (target_calories * 0.20) / 4
    target_carbs = (target_calories * 0.55) / 4
    target_fat = (target_calories * 0.25) / 9

    foods = [dump_doc(food) for food in await Food.find_all().to_list()]
    candidate_foods = [
        food
        for food in foods
        if _dosha_compatible(food, patient.get("vikriti", ""))
        and (patient.get("food_preference") != "veg" or food.get("is_vegetarian"))
        and not check_conflict(food, patient)[0]
    ]
    if not candidate_foods:
        candidate_foods = foods

    by_category = defaultdict(list)
    for food in candidate_foods:
        category = food.get("category", "Other")
        by_category[category].append(food)

    plan = {
        "patient_id": str(patient["_id"]),
        "user_id": doctor_id,
        "template_id": str(template["_id"]),
        "target_calories": round(target_calories, 2),
        "target_protein": round(target_protein, 2),
        "target_carbs": round(target_carbs, 2),
        "target_fat": round(target_fat, 2),
        "notes": f"Auto-generated from template: {template.get('name')}",
        "created_at": datetime.now(timezone.utc),
        "items": []
    }

    total_cal = total_p = total_c = total_f = 0.0

    # Generate for a full week (Day 1 to 7)
    for day in range(1, 8):
        for meal_slot, split in MEAL_SPLITS.items():
            per_meal_target = target_calories * split
            priority_categories = DEFAULT_CATEGORY_ORDER.get(meal_slot, [])

            # Override with template specifics if available
            slot_config = (template.get("meal_slots") or {}).get(meal_slot)
            if isinstance(slot_config, dict) and slot_config.get("categories"):
                priority_categories = slot_config["categories"]

            chosen = None
            for category in priority_categories:
                if by_category.get(category):
                    # Randomize selection within the category for variety
                    chosen = random.choice(by_category[category])
                    break

            if not chosen:
                chosen = random.choice(candidate_foods)

            calories_val = max(chosen.get("calories", 0), 1)
            portion_multiplier = max(per_meal_target / calories_val, 1)
            portion_g = round(100 * min(portion_multiplier, 3), 0)
            factor = portion_g / 100.0

            is_conflict, reason = check_conflict(chosen, patient)
            reasoning = (
                f"{chosen.get('name')} selected for {meal_slot} (Day {day}): {chosen.get('virya') or 'balanced'} virya "
                f"and dosha profile aligned to {patient.get('vikriti')}. {reason}".strip()
            )

            item = {
                "_id": uuid4().hex,
                "food_id": str(chosen["_id"]),
                "food": chosen,  # embed food document
                "meal_slot": meal_slot,
                "day_of_week": day,
                "portion_g": portion_g,
                "calories": round(chosen.get("calories", 0) * factor, 2),
                "protein": round(chosen.get("protein_g", 0) * factor, 2),
                "carbs": round(chosen.get("carbs_g", 0) * factor, 2),
                "fat": round(chosen.get("fat_g", 0) * factor, 2),
                "reasoning": reasoning,
                "is_conflict": is_conflict,
            }
            plan["items"].append(item)
            total_cal += item["calories"]
            total_p += item["protein"]
            total_c += item["carbs"]
            total_f += item["fat"]

    # Note: total_calories stores the average daily calories for the plan
    plan["total_calories"] = round(total_cal / 7.0, 2)
    plan["total_protein"] = round(total_p / 7.0, 2)
    plan["total_carbs"] = round(total_c / 7.0, 2)
    plan["total_fat"] = round(total_f / 7.0, 2)

    plan_doc = DietPlan(**plan)
    await plan_doc.insert()

    return dump_doc(plan_doc)
