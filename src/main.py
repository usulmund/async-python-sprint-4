"""
Модуль с запуском сервиса.
"""

import sys
import asyncio

import uvicorn
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from core import config
from core.config import app_settings

from db.db import engine
from models.base import Base
from api.base_router import router

app = FastAPI(
    title=app_settings.app_title,
    docs_url='/api/openapi',
    openapi_url='/api/openapi.json',
    default_response_class=ORJSONResponse,
)

app.include_router(router)


async def reset_database():
    """
    Корутина для сброса состояния БД.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


"""
* Запуск контейнера с БД:
docker run \
  --rm   \
  --name postgres-fastapi \
  -p 5432:5432 \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=collection \
  -d postgres:14.5

* Сброс базы данных:
    python3 main.py --reset_db

* Тестирование:
    pytest

* Запуск сервиса
    python3 main.py

"""


if __name__ == '__main__':
    if sys.argv[-1] == '--reset_db':
        asyncio.run(reset_database())
    else:
        uvicorn.run(
            'main:app',
            host=config.PROJECT_HOST,
            port=config.PROJECT_PORT,
        )
