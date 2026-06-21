from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from models import Base
import os
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://charles:devpassword@localhost/library")

engine = create_async_engine(DATABASE_URL, echo=True)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async_session = async_sessionmaker(engine, expire_on_commit=False)

async def get_db():
    async with async_session() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_db)]