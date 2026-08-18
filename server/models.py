"""Beanie ODM document models backed by MongoDB."""

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from beanie import Document
from bson import ObjectId
from bson.errors import InvalidId
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from pymongo import IndexModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def to_object_id(value: str) -> Optional[ObjectId]:
    """Convert a string id to an ObjectId, returning None when invalid."""
    try:
        return ObjectId(value)
    except (InvalidId, TypeError, ValueError):
        return None


def dump_doc(doc: Document) -> dict:
    """Serialise a Beanie document to a plain dict with a string `_id`.

    Keeps the exact JSON contract the frontend expects (string ids under
    both `_id` and, where applicable, nested `_id` fields).
    """
    data = doc.model_dump(by_alias=True)
    data["_id"] = str(doc.id)
    return data


class User(Document):
    name: str
    email: EmailStr
    password_hash: str
    role: str = "doctor"
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "users"
        indexes = [IndexModel([("email", 1)], unique=True)]


class Patient(Document):
    name: str
    phone: Optional[str] = None
    age: int
    gender: str
    weight_kg: float
    height_cm: float
    activity_level: str
    vikriti: str
    prakriti: str
    conditions: list[str] = []
    appetite: str
    digestion_strength: str
    food_preference: str
    user_id: str
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "patients"
        indexes = ["user_id", "created_at"]


class Food(Document):
    name: str
    name_hindi: Optional[str] = None
    category: str
    subcategory: Optional[str] = None
    calories: float = 0.0
    protein_g: float = 0.0
    carbs_g: float = 0.0
    fat_g: float = 0.0
    fiber_g: float = 0.0
    rasa: Optional[str] = None
    virya: Optional[str] = None
    vipaka: Optional[str] = None
    vata_effect: int = 0
    pitta_effect: int = 0
    kapha_effect: int = 0
    is_pathya_for: list[str] = []
    is_apathya_for: list[str] = []
    is_vegetarian: bool = True
    season_best: Optional[str] = None
    description: Optional[str] = None

    class Settings:
        name = "foods"
        indexes = ["name", "category"]


class DietTemplate(Document):
    name: str
    target_vikriti: str
    goal: str
    description: Optional[str] = None
    meal_slots: dict[str, Any] = {}

    class Settings:
        name = "diet_templates"
        indexes = [IndexModel([("name", 1)], unique=True)]


class DietPlanItem(BaseModel):
    """Embedded sub-document for a single meal-slot entry inside a plan."""

    model_config = ConfigDict(populate_by_name=True)

    item_id: str = Field(default_factory=lambda: uuid4().hex, alias="_id")
    food_id: str
    food: dict[str, Any] = {}
    meal_slot: str
    day_of_week: int
    portion_g: float
    calories: float = 0.0
    protein: float = 0.0
    carbs: float = 0.0
    fat: float = 0.0
    reasoning: Optional[str] = None
    is_conflict: bool = False


class DietPlan(Document):
    patient_id: str
    user_id: str
    template_id: Optional[str] = None
    total_calories: float = 0.0
    total_protein: float = 0.0
    total_carbs: float = 0.0
    total_fat: float = 0.0
    target_calories: float = 0.0
    target_protein: float = 0.0
    target_carbs: float = 0.0
    target_fat: float = 0.0
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)
    items: list[DietPlanItem] = []

    class Settings:
        name = "diet_plans"
        indexes = ["user_id", "patient_id", "created_at"]
