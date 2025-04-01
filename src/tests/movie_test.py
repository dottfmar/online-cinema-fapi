# isort: skip_file

import asyncio
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database import (
    CertificationModel,
    CommentModel,
    FavoritesModel,
    LikeCommentModel,
    LikeMovieModel,
    MovieModel,
    NotificationModel,
    RatingModel,
    UserGroupEnum,
    UserGroupModel,
    UserModel,
)
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
async def test_get_movies(client):
    async with async_session_maker() as session:
        certification = CertificationModel(
            name="Certification",
        )
        session.add(certification)
        await session.commit()
        await session.refresh(certification)

        movie = MovieModel(
            name="Test movie",
            year=1999,
            time=120,
            imdb=2.2,
            votes=0,
            meta_score=2,
            gross=5,
            description="text",
            price=Decimal(125),
            amount=4,
            certification_id=certification.id,
        )
        session.add(movie)
        await session.commit()
        await session.refresh(movie)
    response = await client.get(f"/movies/")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert response.json() == {
        "movies": [
            {
                "id": 1,
                "name": "Test movie",
                "year": 1999,
                "imdb": 2.2,
                "price": "125.00",
                "certification": "Certification",
            }
        ],
        "prev_page": None,
        "next_page": None,
        "current_page": None,
        "total_pages": 1,
        "total_items": 1,
    }, response.json()


@pytest.mark.asyncio
async def test_get_movie_by_id(client):
    async with async_session_maker() as session:
        certification = CertificationModel(
            name="Certification",
        )
        session.add(certification)
        await session.commit()
        await session.refresh(certification)

        movie = MovieModel(
            name="Test movie",
            year=1999,
            time=120,
            imdb=2.2,
            votes=0,
            meta_score=2,
            gross=5,
            description="text",
            price=Decimal(125),
            amount=4,
            certification_id=certification.id,
        )
        session.add(movie)
        await session.commit()
        await session.refresh(movie)
    response = await client.get(f"/movies/1")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert response.json()["name"] == "Test movie"


@pytest.mark.asyncio
async def test_create_by_moderator_movie(client, moderator_user):
    login_payload = {"username": "moderator@example.com", "password": "se1@PPssword"}
    login_response = await client.post("/login/", data=login_payload)
    assert (
        login_response.status_code == 200
    ), f"Failed to log in as moderator: {login_response.status_code}"
    access_token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {access_token}"}
    movie_payload = {
        "name": "Test movie",
        "year": 1889,
        "time": 1,
        "imdb": 1,
        "votes": 1,
        "meta_score": 1,
        "gross": 1,
        "description": "string",
        "price": 1,
        "amount": 0,
        "certification": "string",
        "genres": ["string"],
        "stars": ["string"],
        "directors": ["string"],
    }
    movie_response = await client.post("/movies/", headers=headers, json=movie_payload)
    assert (
        movie_response.status_code == 201
    ), f"Failed to create movie: {movie_response.status_code}"
    assert movie_response.json()["name"] == "Test movie"
    assert len(movie_response.json()["genres"]) == 1, "Failed to add genres"

    async with async_session_maker() as session:
        movie = await session.execute(
            select(MovieModel).where(MovieModel.name == "Test movie")
        )
        movie = movie.scalars().first()
        assert movie is not None, "Movie not found in the database."
        assert (
            movie.name == "Test movie"
        ), f"Expected movie name 'Test movie', got {movie.name}"


@pytest.mark.asyncio
async def test_update_movie_by_moderator(client, moderator_user):
    async with async_session_maker() as session:
        certification = CertificationModel(
            name="Certification",
        )
        session.add(certification)
        await session.commit()
        await session.refresh(certification)

        movie = MovieModel(
            name="Test movie",
            year=1999,
            time=120,
            imdb=2.2,
            votes=0,
            meta_score=2,
            gross=5,
            description="text",
            price=Decimal(125),
            amount=4,
            certification_id=certification.id,
        )
        session.add(movie)
        await session.commit()
        await session.refresh(movie)
    login_payload = {"username": "moderator@example.com", "password": "se1@PPssword"}
    login_response = await client.post("/login/", data=login_payload)
    assert (
        login_response.status_code == 200
    ), f"Failed to log in as moderator: {login_response.status_code}"
    access_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    movie_payload = {"name": "Updated movie"}
    movie_response = await client.patch(
        "/movies/1", headers=headers, json=movie_payload
    )
    assert (
        movie_response.status_code == 200
    ), f"Failed to update movie: {movie_response.status_code}"

    async with async_session_maker() as session:
        movie = await session.execute(
            select(MovieModel).where(MovieModel.name == "Updated movie")
        )
        movie = movie.scalars().first()
        assert movie is not None, "Movie not found in the database."
        assert (
            movie.name == "Updated movie"
        ), f"Expected movie name 'Updated movie', got {movie.name}"


@pytest.mark.asyncio
async def test_delete_movie_by_moderator(client, moderator_user):
    async with async_session_maker() as session:
        certification = CertificationModel(
            name="Certification",
        )
        session.add(certification)
        await session.commit()
        await session.refresh(certification)

        movie = MovieModel(
            name="Test movie",
            year=1999,
            time=120,
            imdb=2.2,
            votes=0,
            meta_score=2,
            gross=5,
            description="text",
            price=Decimal(125),
            amount=4,
            certification_id=certification.id,
        )
        session.add(movie)
        await session.commit()
        await session.refresh(movie)
    login_payload = {"username": "moderator@example.com", "password": "se1@PPssword"}
    login_response = await client.post("/login/", data=login_payload)
    assert (
        login_response.status_code == 200
    ), f"Failed to log in as moderator: {login_response.status_code}"
    access_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    movie_response = await client.delete("/movies/1", headers=headers)
    assert (
        movie_response.status_code == 204
    ), f"Failed to update movie: {movie_response.status_code}"

    async with async_session_maker() as session:
        movie = await session.execute(
            select(MovieModel).where(MovieModel.name == "Updated movie")
        )
        movie = movie.scalars().all()
        assert len(movie) == 0, "Movie not deleted."


@pytest.mark.asyncio
async def test_like_and_rate_movie(client, moderator_user):
    async with async_session_maker() as session:
        certification = CertificationModel(
            name="Certification",
        )
        session.add(certification)
        await session.commit()
        await session.refresh(certification)

        movie = MovieModel(
            name="Test movie",
            year=1999,
            time=120,
            imdb=2.2,
            votes=0,
            meta_score=2,
            gross=5,
            description="text",
            price=Decimal(125),
            amount=4,
            certification_id=certification.id,
        )
        session.add(movie)
        await session.commit()
        await session.refresh(movie)
    login_payload = {"username": "moderator@example.com", "password": "se1@PPssword"}
    login_response = await client.post("/login/", data=login_payload)
    assert (
        login_response.status_code == 200
    ), f"Failed to log in as moderator: {login_response.status_code}"
    access_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    like_response = await client.post("/movies/1/like", headers=headers)
    assert (
        like_response.status_code == 200
    ), f"Failed to like movie: {like_response.status_code}"
    assert (
        like_response.json()["status"] == True
    ), f"Failed to like movie: {like_response.json()['status']}"

    rating_response = await client.post("/movies/1/rate?rating=1", headers=headers)
    assert (
        rating_response.status_code == 200
    ), f"Failed to rate movie: {rating_response.status_code}"

    async with async_session_maker() as session:
        like = await session.execute(
            select(LikeMovieModel).where(LikeMovieModel.status == True)
        )
        like = like.scalars().first()
        assert like is not None, "Not liked movie."

        rating = await session.execute(
            select(RatingModel).where(RatingModel.rating == 1)
        )
        rating = rating.scalars().first()
        assert rating is not None, "Not rated movie."


@pytest.mark.asyncio
async def test_comment_movie(client, moderator_user):
    async with async_session_maker() as session:
        certification = CertificationModel(
            name="Certification",
        )
        session.add(certification)
        await session.commit()
        await session.refresh(certification)

        movie = MovieModel(
            name="Test movie",
            year=1999,
            time=120,
            imdb=2.2,
            votes=0,
            meta_score=2,
            gross=5,
            description="text",
            price=Decimal(125),
            amount=4,
            certification_id=certification.id,
        )
        session.add(movie)
        await session.commit()
        await session.refresh(movie)
    login_payload = {"username": "moderator@example.com", "password": "se1@PPssword"}
    login_response = await client.post("/login/", data=login_payload)
    assert (
        login_response.status_code == 200
    ), f"Failed to log in as moderator: {login_response.status_code}"
    access_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    comment_payload = {"content": "text"}
    comment_response = await client.post(
        "/movies/1/comments", headers=headers, json=comment_payload
    )
    assert (
        comment_response.status_code == 201
    ), f"Failed to like movie: {comment_response.status_code}"
    assert (
        comment_response.json()["content"] == "text"
    ), f"Failed to comment movie: {comment_response.json()['content']}"

    async with async_session_maker() as session:
        comment = await session.execute(
            select(CommentModel).where(CommentModel.content == "text")
        )
        comment = comment.scalars().first()
        assert comment is not None, "Not commented movie."


@pytest.mark.asyncio
async def test_like_and_reply_comment_movie_with_notification(client, moderator_user):
    async with async_session_maker() as session:
        certification = CertificationModel(
            name="Certification",
        )
        session.add(certification)
        await session.commit()
        await session.refresh(certification)

        movie = MovieModel(
            name="Test movie",
            year=1999,
            time=120,
            imdb=2.2,
            votes=0,
            meta_score=2,
            gross=5,
            description="text",
            price=Decimal(125),
            amount=4,
            certification_id=certification.id,
        )
        session.add(movie)
        await session.commit()
        await session.refresh(movie)
    login_payload = {"username": "moderator@example.com", "password": "se1@PPssword"}
    login_response = await client.post("/login/", data=login_payload)
    assert (
        login_response.status_code == 200
    ), f"Failed to log in as moderator: {login_response.status_code}"
    access_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    comment_payload = {"content": "text"}
    comment_response = await client.post(
        "/movies/1/comments", headers=headers, json=comment_payload
    )
    assert (
        comment_response.status_code == 201
    ), f"Failed to like movie: {comment_response.status_code}"

    comment_like_response = await client.post(
        "/movies/1/comments/1/like", headers=headers
    )
    assert (
        comment_like_response.status_code == 200
    ), f"Failed to like comment: {comment_like_response.status_code}"
    assert (
        comment_like_response.json()["status"] == "success"
    ), f"Failed to like comment: {comment_like_response.json()['status']}"

    reply_payload = {"content": "reply"}
    comment_reply_response = await client.post(
        "/movies/1/comments/1/reply", headers=headers, json=reply_payload
    )
    assert (
        comment_reply_response.status_code == 201
    ), f"Failed to reply comment: {comment_reply_response.status_code}"
    assert (
        comment_reply_response.json()["content"] == "Reply to comment 1: reply"
    ), f"Failed to reply comment: {comment_reply_response.json()['content']}"

    async with async_session_maker() as session:
        comment = await session.execute(
            select(LikeCommentModel).where(LikeCommentModel.status == True)
        )
        comment = comment.scalars().first()
        assert comment is not None, "Not commented movie."

        reply = await session.execute(
            select(CommentModel).where(
                CommentModel.content == "Reply to comment 1: reply"
            )
        )
        reply = reply.scalars().first()
        assert reply is not None, "Not commented movie."

        like = await session.execute(select(LikeCommentModel))
        like = like.scalars().first()
        assert like is not None, "Not liked comment."

        notification = await session.execute(select(NotificationModel))
        notification = notification.scalars().all()
        assert notification is not None, "Not notified movie."
        assert len(notification) == 2, "Not notified movie."


@pytest.mark.asyncio
async def test_add_to_favourite(client, moderator_user):
    async with async_session_maker() as session:
        certification = CertificationModel(
            name="Certification",
        )
        session.add(certification)
        await session.commit()
        await session.refresh(certification)

        movie = MovieModel(
            name="Test movie",
            year=1999,
            time=120,
            imdb=2.2,
            votes=0,
            meta_score=2,
            gross=5,
            description="text",
            price=Decimal(125),
            amount=4,
            certification_id=certification.id,
        )
        session.add(movie)
        await session.commit()
        await session.refresh(movie)
    login_payload = {"username": "moderator@example.com", "password": "se1@PPssword"}
    login_response = await client.post("/login/", data=login_payload)
    assert (
        login_response.status_code == 200
    ), f"Failed to log in as moderator: {login_response.status_code}"
    access_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    favourite_response = await client.post("/movies/1/favorite", headers=headers)
    assert (
        favourite_response.status_code == 200
    ), f"Failed to add movie to favourite: {favourite_response.status_code}"
    assert (
        favourite_response.json()["status"] == True
    ), f"Failed to add movie: {favourite_response.json()['status']}"

    async with async_session_maker() as session:
        favourite = await session.execute(
            select(FavoritesModel).where(FavoritesModel.status == True)
        )
        favourite = favourite.scalars().first()
        assert favourite is not None, "Not movie in favourite."
