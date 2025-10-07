import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.core.security import hash_password

@pytest.fixture
async def user_created(db_session: AsyncSession):
    hashed_password = hash_password("password123")
    user = User(email="user@example.com", password=hashed_password)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    yield user
    await db_session.delete(user)
    await db_session.commit()


async def test_register_user_exists(client, user_created):
    response = client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "password123"},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Email already registered"}


async def test_register_user_success(client, db_session: AsyncSession):
    response = client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "password123"},
    )
    assert response.status_code == 201
    assert response.json()["email"] == "user@example.com"

    user = await db_session.execute(
        select(User).filter(User.email == "user@example.com")
    )
    user = user.scalars().first()
    assert user is not None
    assert user.email == "user@example.com"

    await db_session.delete(user)
    await db_session.commit()


async def test_login_user_not_exists(client):
    response = client.post(
        "/auth/login",
        json={"email": "nonexistent@example.com", "password": "password123"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect email or password"}


async def test_login_user_wrong_password(client, user_created):
    response = client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect email or password"}


async def test_login_user(client, user_created):
    response = client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert "access_token" in response.json()
