# isort: skip_file

import asyncio

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database import StarModel, UserGroupEnum, UserGroupModel, UserModel
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

        groups = [
            {"name": UserGroupEnum.USER},
            {"name": UserGroupEnum.MODERATOR},
            {"name": UserGroupEnum.ADMIN},
        ]
        for group in groups:
            await conn.execute(
                UserGroupModel.__table__.insert().values(name=group["name"])
            )

    yield

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def moderator_user():
    async with async_session_maker() as session:
        moderator_group = await session.execute(
            select(UserGroupModel).where(UserGroupModel.name == UserGroupEnum.MODERATOR)
        )
        moderator_group_id = moderator_group.scalars().first().id
        moderator = UserModel.create(
            email="moderator@example.com",
            raw_password="se1@PPssword",
            group_id=moderator_group_id,
        )

        session.add(moderator)
        moderator.is_active = True
        await session.commit()
        await session.refresh(moderator)

    yield moderator


@pytest_asyncio.fixture(scope="function")
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as async_client:
        yield async_client


@pytest.mark.asyncio
async def test_get_genres(client):
    async with async_session_maker() as session:
        star_1 = StarModel(name="Actor 1")
        session.add(star_1)
        await session.commit()
        await session.refresh(star_1)
    async with async_session_maker() as session:
        star_2 = StarModel(name="Actor 2")
        session.add(star_2)
        await session.commit()
        await session.refresh(star_2)
    response = await client.get(f"/stars/")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert response.json() == [
        {"id": 1, "name": "Actor 1"},
        {"id": 2, "name": "Actor 2"},
    ], f"Unexpected response: {response.json()}"


@pytest.mark.asyncio
async def test_create_star_by_moderator(client, moderator_user):
    login_payload = {"username": "moderator@example.com", "password": "se1@PPssword"}
    login_response = await client.post("/login/", data=login_payload)
    assert (
        login_response.status_code == 200
    ), f"Failed to log in as moderator: {login_response.status_code}"
    access_token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {access_token}"}
    star_payload = {"name": "Actor"}
    star_response = await client.post("/stars/", json=star_payload, headers=headers)
    assert (
        star_response.status_code == 201
    ), f"Failed to create genre: {star_response.status_code}"
    assert (
        star_response.json()["name"] == "Actor"
    ), f"Unexpected response: {star_response.json()}"

    async with async_session_maker() as session:
        star = await session.execute(select(StarModel).where(StarModel.name == "Actor"))
        star = star.scalars().first()
        assert star is not None, "Star not found in the database."
        assert star.name == "Actor", f"Expected star name 'Actor', got {star.name}"


@pytest.mark.asyncio
async def test_update_genre_by_moderator(client, moderator_user):
    async with async_session_maker() as session:
        star = StarModel(name="Actor")
        session.add(star)
        await session.commit()
        await session.refresh(star)

    login_payload = {"username": "moderator@example.com", "password": "se1@PPssword"}
    login_response = await client.post("/login/", data=login_payload)
    assert (
        login_response.status_code == 200
    ), f"Failed to log in as moderator: {login_response.status_code}"
    access_token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {access_token}"}
    star_payload = {"name": "Test"}
    star_response = await client.put("/stars/1/", json=star_payload, headers=headers)
    assert (
        star_response.status_code == 200
    ), f"Failed to update star: {star_response.status_code}"
    assert (
        star_response.json()["name"] == "Test"
    ), f"Unexpected response: {star_response.json()}"

    async with async_session_maker() as session:
        star = await session.execute(select(StarModel).where(StarModel.name == "Test"))
        star = star.scalars().first()
        assert star is not None, "Star not found in the database."
        assert star.name == "Test", f"Expected star name 'Test', got {star.name}"


@pytest.mark.asyncio
async def test_delete_genre_by_moderator(client, moderator_user):
    async with async_session_maker() as session:
        star = StarModel(name="Actor")
        session.add(star)
        await session.commit()
        await session.refresh(star)

    login_payload = {"username": "moderator@example.com", "password": "se1@PPssword"}
    login_response = await client.post("/login/", data=login_payload)
    assert (
        login_response.status_code == 200
    ), f"Failed to log in as moderator: {login_response.status_code}"
    access_token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {access_token}"}
    star_response = await client.delete("/stars/1/", headers=headers)
    assert (
        star_response.status_code == 204
    ), f"Failed to delete star: {star_response.status_code}"

    async with async_session_maker() as session:
        star = await session.execute(select(StarModel))
        star = star.scalars().all()
        assert len(star) == 0, f"Star not deleted"
