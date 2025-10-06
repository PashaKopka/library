import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.user import create_user, get_user, get_user_by_email
from app.models.user import User
from app.schemas.user import UserCreate


@pytest.fixture
async def user_created(db_session: AsyncSession):
    user = User(
        email="test@example.com",
        password="somehashedpassword",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    yield user
    await db_session.delete(user)
    await db_session.commit()


async def test_get_user_by_id(db_session, user_created):
    user = await get_user(db_session, user_created.id)
    assert user is not None
    assert user.email == user_created.email


async def test_get_user_by_invalid_id(db_session):
    user = await get_user(db_session, 9999)
    assert user is None


async def test_get_user_by_negative_id(db_session):
    user = await get_user(db_session, -1)
    assert user is None


async def test_get_user_by_email(db_session, user_created):
    user = await get_user_by_email(db_session, user_created.email)
    assert user is not None
    assert user.email == user_created.email


async def test_get_user_by_invalid_email(db_session):
    user = await get_user_by_email(db_session, "invalid@example.com")
    assert user is None


async def test_get_user_by_empty_email(db_session):
    user = await get_user_by_email(db_session, "")
    assert user is None


async def test_create_user(db_session):
    user = await create_user(
        db_session,
        UserCreate(email="test@example.com", password="somehashedpassword"),
    )
    assert user is not None
    assert user.email == "test@example.com"

    await db_session.delete(user)
    await db_session.commit()
