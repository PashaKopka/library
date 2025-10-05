from pydantic import BaseModel, Field


class UserBase(BaseModel):
    email: str = Field(..., examples=["johndoe@example.com"], max_length=255)


class UserCreate(UserBase):
    password: str = Field(..., examples=["strong_password"], min_length=8)


class UserRead(UserBase):
    id: int

    class Config:
        from_attributes = True


class UserUpdate(UserBase):
    password: str = Field(..., examples=["strong_password"], min_length=8)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
