from fastapi import APIRouter, Depends, HTTPException

import schemas
from auth import get_current_user
from models import DietPlan, Patient, User, dump_doc, to_object_id

router = APIRouter(prefix="/api/patients", tags=["patients"])


@router.get("", response_model=list[schemas.PatientOut])
async def list_patients(
    current_user: User = Depends(get_current_user),
):
    patients = (
        await Patient.find(Patient.user_id == str(current_user.id))
        .sort("-created_at")
        .to_list()
    )
    return [dump_doc(p) for p in patients]


@router.post("", response_model=schemas.PatientOut)
async def create_patient(
    payload: schemas.PatientCreate,
    current_user: User = Depends(get_current_user),
):
    patient = Patient(**payload.model_dump(), user_id=str(current_user.id))
    await patient.insert()
    return dump_doc(patient)


@router.get("/{patient_id}", response_model=schemas.PatientOut)
async def get_patient(
    patient_id: str,
    current_user: User = Depends(get_current_user),
):
    oid = to_object_id(patient_id)
    patient = (
        await Patient.find_one(Patient.id == oid, Patient.user_id == str(current_user.id))
        if oid
        else None
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return dump_doc(patient)


@router.put("/{patient_id}", response_model=schemas.PatientOut)
async def update_patient(
    patient_id: str,
    payload: schemas.PatientUpdate,
    current_user: User = Depends(get_current_user),
):
    oid = to_object_id(patient_id)
    patient = (
        await Patient.find_one(Patient.id == oid, Patient.user_id == str(current_user.id))
        if oid
        else None
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if update_data:
        for field, value in update_data.items():
            setattr(patient, field, value)
        await patient.save()

    return dump_doc(patient)


@router.delete("/{patient_id}")
async def delete_patient(
    patient_id: str,
    current_user: User = Depends(get_current_user),
):
    oid = to_object_id(patient_id)
    patient = (
        await Patient.find_one(Patient.id == oid, Patient.user_id == str(current_user.id))
        if oid
        else None
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    await patient.delete()
    await DietPlan.find(DietPlan.patient_id == patient_id).delete()
    return {"success": True}
