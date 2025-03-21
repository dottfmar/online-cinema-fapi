from fastapi import FastAPI
from routers import movie_router
app = FastAPI(
    title="Online cinema",
)
api_version_prefix = "/api/v1"

app.include_router(movie_router, prefix=f"{api_version_prefix}/theater", tags=["theater"])
