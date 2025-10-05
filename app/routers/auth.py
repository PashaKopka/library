from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.crud.user import create_user, get_user_by_email
from app.schemas.user import Token, UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = await get_user_by_email(db, email=payload.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )

    new_user = await create_user(db, user=payload)
    return UserRead.model_validate(new_user)


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
async def login_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = await get_user_by_email(db, email=payload.email)
    if not db_user or not verify_password(payload.password, str(db_user.password)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = create_access_token(data={"email": db_user.email})

    return Token(access_token=access_token)
