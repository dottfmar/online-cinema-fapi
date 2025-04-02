# isort: skip_file

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

ASYNC_DATABASE_URL = os.getenv("ASYNC_DATABASE_URL")
if not ASYNC_DATABASE_URL:
    raise ValueError("ASYNC_DATABASE_URL is not set in the environment variables")

# Creating an asynchronous engine
async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=True)

# Creating a session factory
async_session_maker = async_sessionmaker(
    async_engine, expire_on_commit=False, class_=AsyncSession
)


async def get_db():
    async with async_session_maker() as session:
        yield session


DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the environment variables")

engine = create_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_sync():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
