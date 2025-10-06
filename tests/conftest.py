import asyncio
from contextlib import ExitStack

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlalchemy_utils import create_database, database_exists, drop_database

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app as actual_app


@pytest.fixture(scope="session")
def engine():
    engine = create_async_engine(settings.test_database_url, poolclass=NullPool)
    yield engine
    engine.sync_engine.dispose()


def recreate_test_database():
    # We need to change url to sync driver for sqlalchemy_utils to work
    sync_db_url = settings.test_database_url.replace("postgresql+asyncpg", "postgresql")

    if database_exists(sync_db_url):
        drop_database(sync_db_url)
    create_database(sync_db_url)


@pytest.fixture(scope="session", autouse=True)
async def init_test_db(engine):
    recreate_test_database()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    drop_database(settings.test_database_url)


@pytest.fixture(scope="session")
async def sessionmanager(engine):
    yield async_sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        expire_on_commit=False,
    )


@pytest.fixture(scope="function")
async def db_session(sessionmanager):
    async with sessionmanager() as session:
        try:
            await session.begin()
            yield session
        finally:
            await session.rollback()


@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture()
def app(sessionmanager):
    async def override_get_db():
        async with sessionmanager() as db:
            yield db

    actual_app.dependency_overrides[get_db] = override_get_db
    with ExitStack():
        yield actual_app


@pytest.fixture()
def client(app):
    with TestClient(app) as c:
        yield c
