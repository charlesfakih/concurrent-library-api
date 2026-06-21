import asyncio

import pytest
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

async def test_create_book(setup_database, client):
    response = await client.post(
        "/books",
        json={"title": "Mockingbird", "author": "Whatever", "total_copies": 10}
    )
    assert response.status_code == 201
    actual_response = response.json()
    assert actual_response["available_copies"] == actual_response["total_copies"]

async def test_borrow_book_success(setup_database, client):
    response_create = await client.post(
        "/books",
        json={"title": "Hey", "author": "Hey", "total_copies": 1}
    )

    assert response_create.status_code == 201
    actual_response_create = response_create.json()
    book_id = actual_response_create["id"]
    response_borrow = await client.post(
        f"/books/{book_id}/borrow"
    )
    assert response_borrow.status_code == 201
    actual_response_borrow = response_borrow.json()
    assert actual_response_borrow["book_id"] == book_id
    assert actual_response_borrow["returned"] == False

async def test_borrow_book_overbooking_rejected(setup_database, client):
    response_create = await client.post(
        "/books",
        json={"title": "Hey", "author": "Hey", "total_copies": 1}
    )
    actual_response_create = response_create.json()
    book_id = actual_response_create["id"]
    response_borrow_first = await client.post(
        f"/books/{book_id}/borrow"
    )
    response_borrow_second = await client.post(
        f"/books/{book_id}/borrow"
    )
    assert response_borrow_second.status_code == 409

async def test_borrow_book_concurrent_overbooking_rejected(setup_database, client):
    response_create = await client.post(
        "/books",
        json={"title": "Hey", "author": "Hey", "total_copies": 1}
    )
    actual_response_create = response_create.json()
    book_id = actual_response_create["id"]

    results = await asyncio.gather(
        client.post(f"/books/{book_id}/borrow"),
        client.post(f"/books/{book_id}/borrow")
    )

    success_count = sum(1 for r in results if r.status_code == 201)
    conflict_count = sum(1 for r in results if r.status_code == 409)
    assert success_count == 1
    assert conflict_count == 1

async def test_return_copy(setup_database, client):
    response_create = await client.post(
        "/books",
        json={"title": "Hey", "author": "Hey", "total_copies": 1}
    )
    actual_response_create = response_create.json()
    book_id = actual_response_create["id"]
    response_borrow = await client.post(
        f"/books/{book_id}/borrow"
    )
    actual_response_borrow = response_borrow.json()
    loan_id = actual_response_borrow["id"]
    response_return = await client.post(
        f"/loans/{loan_id}/return"
    )
    actual_response_return = response_return.json()
    assert response_return.status_code == 200
    assert actual_response_return["returned"] == True
