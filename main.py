from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager

from sqlalchemy import select
from database import SessionDep, init_db
from routers import auth, books, loans

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health_check(session: SessionDep):
    try:
        await session.execute(select(1))
        return {"status": "healthy"}
    except Exception:
        raise HTTPException(status_code=503, detail="Database unavailable")

app.include_router(books.router)
app.include_router(loans.router)
app.include_router(auth.router)