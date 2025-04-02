# isort: skip_file
import os
import sys

from fastapi import FastAPI

from routers import (
    accounts_router,
    cart_router,
    order_router,
    genre_router,
    movies_router,
    payment_router,
    profiles_router,
    star_router,
)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))
app = FastAPI(
    title="Online cinema",
)
app.include_router(payment_router)
app.include_router(accounts_router)
app.include_router(order_router)
app.include_router(cart_router)
app.include_router(genre_router)

app.include_router(accounts_router)
app.include_router(profiles_router)
app.include_router(genre_router)
app.include_router(star_router)
app.include_router(movies_router)
