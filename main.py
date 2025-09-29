from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router as app_router
from app.core.container import Container


container = Container()

@asynccontextmanager
async def lifespan(_: FastAPI):
    db_connection = container.db_connection()
    await db_connection.create_pool()
    print("✅ Database connection pool created")

    yield

    await db_connection.close_pool()
    print("🛑 Database connection pool closed")


app = FastAPI(
    title="Phishing Forge API",
    version="0.1.0",
    lifespan=lifespan,
)

app.container = container

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(app_router)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
