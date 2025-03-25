import asyncio
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.movie import MovieModel
from src.sessions.session_maker import async_session_maker


async def load_data():
    async with async_session_maker() as session:
        await add_movies(session)


async def add_movies(session: AsyncSession):
    movie1 = MovieModel(
        uuid=uuid.uuid4(),
        name="The Matrix",
        year=1999,
        time=136,
        imdb=8.7,
        votes=1800000,
        meta_score=73,
        gross=171479930,
        description="A computer hacker learns about the true nature of reality.",
        price=12.99,
    )

    movie2 = MovieModel(
        uuid=uuid.uuid4(),
        name="Inception",
        year=2010,
        time=148,
        imdb=8.8,
        votes=2200000,
        meta_score=74,
        gross=292576195,
        description="A thief who enters the dreams of others to steal secrets.",
        price=14.99,
    )

    session.add_all([movie1, movie2])
    await session.commit()
    print("Movies loaded successfully.")


if __name__ == "__main__":
    asyncio.run(load_data())
