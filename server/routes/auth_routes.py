from fastapi import APIRouter, HTTPException, status

import schemas
from auth import create_access_token, get_password_hash, is_legacy_hash, verify_password
from models import User, dump_doc

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=schemas.UserOut)
async def register(payload: schemas.UserCreate):
    normalized_email = payload.email.lower().strip()
    existing = await User.find_one(User.email == normalized_email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        name=payload.name.strip(),
        email=normalized_email,
        password_hash=get_password_hash(payload.password),
        role="doctor",
    )
    await user.insert()
    return dump_doc(user)


@router.post("/login", response_model=schemas.Token)
async def login(payload: schemas.LoginRequest):
    user = await User.find_one(User.email == payload.email.lower().strip())
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if is_legacy_hash(user.password_hash):
        user.password_hash = get_password_hash(payload.password)
        await user.save()
    token = create_access_token(str(user.id))
    return schemas.Token(access_token=token)
