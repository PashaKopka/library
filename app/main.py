from typing import Union

from fastapi import FastAPI

from app.routers import auth, book

app = FastAPI()

app.include_router(auth.router)
app.include_router(book.router)


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
async def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}
