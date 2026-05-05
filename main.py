import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router as app_router
from app.core.container import Container

logger = logging.getLogger("phishforge.main")


def configure_logging() -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO)


def create_lifespan(container: Container):
    @asynccontextmanager
    async def lifespan(_: FastAPI):
        db_connection = container.db_connection()
        await db_connection.create_pool()
        logger.info("Database connection pool created")

        try:
            yield
        finally:
            await db_connection.close_pool()
            logger.info("Database connection pool closed")

    return lifespan


def create_app() -> FastAPI:
    configure_logging()
    container = Container()

    app = FastAPI(
        title="Phishing Forge API",
        version="0.1.0",
        lifespan=create_lifespan(container),
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

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
