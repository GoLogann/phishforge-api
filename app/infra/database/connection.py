from contextlib import asynccontextmanager

import asyncpg

from app.core.config import settings


class DatabaseConnection:
    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        self._pool = None
        self._config = {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "database": database
        }

    async def create_pool(self):
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                **self._config,
                min_size=1,
                max_size=10,
                command_timeout=60
            )
        return self._pool

    async def close_pool(self):
        if self._pool:
            await self._pool.close()
            self._pool = None

    @asynccontextmanager
    async def get_connection(self):
        pool = await self.create_pool()
        async with pool.acquire() as connection:
            yield connection

    @property
    def pool(self):
        return self._pool


async def get_db_pool():
    """Função utilitária para criar um pool de conexões com o banco."""
    return await asyncpg.create_pool(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
        min_size=1,
        max_size=10,
        command_timeout=60
    )

