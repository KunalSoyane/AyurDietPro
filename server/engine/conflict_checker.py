def check_conflict(food: dict, patient: dict) -> tuple[bool, str]:
    vikriti = (patient.get("vikriti") or "").lower()
    conditions = [c.lower() for c in (patient.get("conditions") or [])]

    if vikriti == "pitta" and food.get("pitta_effect", 0) > 0:
        return True, "This food increases Pitta for a Pitta imbalance."
    if vikriti == "vata":
        if food.get("vata_effect", 0) > 0:
            return True, "This food increases Vata for a Vata imbalance."
        if (food.get("virya") or "").lower() == "cooling":
            return True, "Cooling virya may aggravate Vata."
    if vikriti == "kapha" and food.get("kapha_effect", 0) > 0:
        return True, "This food increases Kapha for a Kapha imbalance."

    apathya = [a.lower() for a in (food.get("is_apathya_for") or [])]
    for condition in conditions:
        if condition in apathya:
            return True, f"This food is contraindicated for {condition}."
    return False, ""

