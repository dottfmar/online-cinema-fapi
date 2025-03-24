import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv(
    "ASYNC_DATABASE_URL",
    "postgresql+asyncpg://cinema_owner:npg_1ONjELg"
    "F6sry@ep-calm-cell-a2y1mtn0-pooler.eu-central-1.aws.neon.tech/cinema",
)

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")

engine = create_async_engine(DATABASE_URL, future=True, echo=True)

AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
