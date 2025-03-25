import os
import sys

from fastapi import FastAPI

from routers import accounts_router, genres_router, payment_router

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))
app = FastAPI(
    title="Online cinema",
)
app.include_router(payment_router)
app.include_router(accounts_router)
app.include_router(genres_router)
