import os
import sys

from fastapi import FastAPI

from routers import payment_router

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))
app = FastAPI(
    title="Online cinema",
)
app.include_router(payment_router)
