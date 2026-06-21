from typing import Annotated

from fastapi import Depends
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from main import app
from models import Base
from database import get_db

TEST_DATABASE_URL = "postgresql+asyncpg://charles:devpassword@localhost/library_test"


@pytest_asyncio.fixture
async def setup_database():
    test_engine = create_async_engine(TEST_DATABASE_URL)
    TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)
    async def override_get_db():
        async with TestSessionLocal() as session:
            yield session
    async with test_engine.begin() as conn:
        
        await conn.run_sync(Base.metadata.create_all)
    app.dependency_overrides[get_db] = override_get_db
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


