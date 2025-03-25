# isort: skip_file

import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


load_dotenv()

DATABASE_URL = os.getenv("ASYNC_DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the environment variables")

# Creating an asynchronous engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Creating a session factory
async_session_maker = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)
