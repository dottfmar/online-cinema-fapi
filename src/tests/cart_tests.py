# isort: skip_file

import asyncio
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database import MovieModel, UserModel
from database.models.base import Base
from dependencies import get_db
from main import app

ASYNC_DATABASE_URL_TEST = "sqlite+aiosqlite:///./test.db"
async_engine = create_async_engine(ASYNC_DATABASE_URL_TEST, echo=True)
async_session_maker = async_sessionmaker(
    async_engine, expire_on_commit=False, class_=AsyncSession
)


async def override_get_db():
    async with async_session_maker() as session:
        yield session


app.dependency_overrides = {get_db: override_get_db}


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_test_database():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def movie():
    async with async_session_maker() as session:
        movie = MovieModel(
            name="Test Movie",
            year=2023,
            time=120,
            imdb=7.8,
            votes=15000,
            description="Test movie description",
            price=Decimal(9.99),
            certification_id=1,
        )
        session.add(movie)
        await session.commit()
        await session.refresh(movie)
    return movie


@pytest_asyncio.fixture(scope="function")
async def user():
    async with async_session_maker() as session:
        group_id = 1
        user = UserModel.create(
            email="user@example.com", raw_password="Password123@", group_id=group_id
        )
        user.is_active = True
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as async_client:
        yield async_client


@pytest.mark.asyncio
async def test_get_empty_cart(client, user):
    login_payload = {"username": "user@example.com", "password": "Password123@"}
    login_response = await client.post("/login/", data=login_payload)
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {access_token}"}
    response = await client.get("/cart/", headers=headers)
    assert response.status_code == 404
    assert response.json() == {"detail": "Cart not found"}


@pytest.mark.asyncio
async def test_add_movie_to_cart(client, user, movie):
    login_payload = {"username": "user@example.com", "password": "Password123@"}
    login_response = await client.post("/login/", data=login_payload)
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {access_token}"}
    add_movie_payload = {"movie_id": movie.id}
    response = await client.post("/cart/", json=add_movie_payload, headers=headers)
    assert response.status_code == 200

    print(response.json())

    assert response.json()["items"][0]["movie_id"] == movie.id


@pytest.mark.asyncio
async def test_get_cart(client, user, movie):
    login_payload = {"username": "user@example.com", "password": "Password123@"}
    login_response = await client.post("/login/", data=login_payload)
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {access_token}"}
    add_movie_payload = {"movie_id": movie.id}
    await client.post("/cart/", json=add_movie_payload, headers=headers)

    response = await client.get("/cart/", headers=headers)
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["movie_id"] == movie.id


@pytest.mark.asyncio
async def test_remove_movie_from_cart(client, user, movie):
    login_payload = {"username": "user@example.com", "password": "Password123@"}
    login_response = await client.post("/login/", data=login_payload)
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {access_token}"}
    add_movie_payload = {"movie_id": movie.id}
    await client.post("/cart/", json=add_movie_payload, headers=headers)

    response = await client.delete(f"/cart/?movie_id={movie.id}", headers=headers)
    assert response.status_code == 200
    assert len(response.json()["items"]) == 0


@pytest.mark.asyncio
async def test_clear_cart(client, user, movie):
    login_payload = {"username": "user@example.com", "password": "Password123@"}
    login_response = await client.post("/login/", data=login_payload)
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {access_token}"}
    add_movie_payload = {"movie_id": movie.id}
    await client.post("/cart/", json=add_movie_payload, headers=headers)

    response = await client.delete("/cart/clear/", headers=headers)
    assert response.status_code == 200
    assert len(response.json()["items"]) == 0


@pytest.mark.asyncio
async def test_checkout_cart(client, user, movie):
    login_payload = {"username": "user@example.com", "password": "Password123@"}
    login_response = await client.post("/login/", data=login_payload)
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {access_token}"}
    add_movie_payload = {"movie_id": movie.id}
    await client.post("/cart/", json=add_movie_payload, headers=headers)

    response = await client.post("/cart/checkout/", headers=headers)
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    assert response.json()["status"] == "checked_out"
