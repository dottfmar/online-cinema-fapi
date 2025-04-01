# isort: skip_file

import asyncio

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database import GenreModel, UserGroupEnum, UserGroupModel, UserModel
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
async def test_genres_empty_db(client):
    response = await client.get("/genres/")
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    assert response.json() == {
        "detail": "No genres found."
    }, f"Unexpected response: {response.json()}"


@pytest.mark.asyncio
async def test_get_genres(client):
    async with async_session_maker() as session:
        genre_1 = GenreModel(name="Action")
        session.add(genre_1)
        await session.commit()
        await session.refresh(genre_1)
    async with async_session_maker() as session:
        genre_2 = GenreModel(name="Drama")
        session.add(genre_2)
        await session.commit()
        await session.refresh(genre_2)
    response = await client.get(f"/genres/")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert response.json() == {
        "genres": [
            {"id": 1, "name": "Action", "movie_count": 0},
            {"id": 2, "name": "Drama", "movie_count": 0},
        ]
    }


@pytest.mark.asyncio
async def test_get_genre_by_id(client):
    async with async_session_maker() as session:
        genre = GenreModel(name="Action")
        session.add(genre)
        await session.commit()
        await session.refresh(genre)

    response = await client.get(f"/genres/{genre.id}/")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert (
        response.json()["name"] == "Action"
    ), f"Unexpected response: {response.json()}"
    assert response.json()["related_movies"] == []


@pytest.mark.asyncio
async def test_create_genre_by_moderator(client, moderator_user):
    login_payload = {"username": "moderator@example.com", "password": "se1@PPssword"}
    login_response = await client.post("/login/", data=login_payload)
    assert (
        login_response.status_code == 200
    ), f"Failed to log in as moderator: {login_response.status_code}"
    access_token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {access_token}"}
    genre_payload = {"name": "Drama"}
    genre_response = await client.post("/genres/", json=genre_payload, headers=headers)
    assert (
        genre_response.status_code == 201
    ), f"Failed to create genre: {genre_response.status_code}"
    assert (
        genre_response.json()["name"] == "Drama"
    ), f"Unexpected response: {genre_response.json()}"

    async with async_session_maker() as session:
        genre = await session.execute(
            select(GenreModel).where(GenreModel.name == "Drama")
        )
        genre = genre.scalars().first()
        assert genre is not None, "Genre not found in the database."
        assert genre.name == "Drama", f"Expected genre name 'Drama', got {genre.name}"


@pytest.mark.asyncio
async def test_update_genre_by_moderator(client, moderator_user):
    async with async_session_maker() as session:
        genre = GenreModel(name="Action")
        session.add(genre)
        await session.commit()
        await session.refresh(genre)

    login_payload = {"username": "moderator@example.com", "password": "se1@PPssword"}
    login_response = await client.post("/login/", data=login_payload)
    assert (
        login_response.status_code == 200
    ), f"Failed to log in as moderator: {login_response.status_code}"
    access_token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {access_token}"}
    genre_payload = {"name": "Dorama"}
    genre_response = await client.put("/genres/1/", json=genre_payload, headers=headers)
    assert (
        genre_response.status_code == 200
    ), f"Failed to update genre: {genre_response.status_code}"
    assert (
        genre_response.json()["name"] == "Dorama"
    ), f"Unexpected response: {genre_response.json()}"

    async with async_session_maker() as session:
        genre = await session.execute(
            select(GenreModel).where(GenreModel.name == "Dorama")
        )
        genre = genre.scalars().first()
        assert genre is not None, "Genre not found in the database."
        assert genre.name == "Dorama", f"Expected genre name 'Drama', got {genre.name}"


@pytest.mark.asyncio
async def test_delete_genre_by_moderator(client, moderator_user):
    async with async_session_maker() as session:
        genre = GenreModel(name="Action")
        session.add(genre)
        await session.commit()
        await session.refresh(genre)

    login_payload = {"username": "moderator@example.com", "password": "se1@PPssword"}
    login_response = await client.post("/login/", data=login_payload)
    assert (
        login_response.status_code == 200
    ), f"Failed to log in as moderator: {login_response.status_code}"
    access_token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {access_token}"}
    genre_response = await client.delete("/genres/1/", headers=headers)
    assert (
        genre_response.status_code == 204
    ), f"Failed to delete genre: {genre_response.status_code}"

    async with async_session_maker() as session:
        genre = await session.execute(select(GenreModel))
        genre = genre.scalars().all()
        assert len(genre) == 0, f"Genre not deleted"
