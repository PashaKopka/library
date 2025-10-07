from contextlib import asynccontextmanager
from typing import Union

from fastapi import FastAPI
from sqlalchemy import text

from app.core.database import async_session
from app.routers import auth, book


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    async with async_session() as session:
        await session.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
        await session.commit()
    yield
    print("Shutting down...")


app = FastAPI(lifespan=lifespan)

app.include_router(auth.router)
app.include_router(book.router)
