from app.api import router
from fastapi import FastAPI

app = FastAPI(
    title="RAG Retrieval Service",
)


app.include_router(
    router,
    prefix="/api/retrieval",
)
