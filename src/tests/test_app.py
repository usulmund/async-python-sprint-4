"""
Модуль с тестами.
"""
import os

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import NullPool
import pytest

from db.db import get_session
from models.base import Base
from main import app


DSN = os.getenv(
    'DATABASE_DSN',
    default='postgresql+asyncpg://postgres:postgres@localhost:1234/postgres'
)
test_engine = create_async_engine(
    DSN,
    echo=True,
    future=True,
    poolclass=NullPool
)

test_async_session = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.mark.asyncio
async def test_create_database():
    """
    Корутина для создания тестовой БД.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def override_get_session():
    async with test_async_session() as session:
        yield session


app.dependency_overrides[get_session] = override_get_session
client = TestClient(app)


def test_root():
    get_user_data_point = app.url_path_for('get_user_data')
    response = client.get(get_user_data_point)
    assert response.status_code == 200


def test_auth():
    check_auth_point = app.url_path_for('check_auth_data_to_log_in')
    response = client.post(
        check_auth_point,
        json={
            'username': 'some_name',
            'password': 'some_password'
        }
    )
    assert response.status_code == 200
    assert response.json() == {'message': 'Welcome, some_name!'}


def test_url_shorter():
    make_short_point = app.url_path_for('make_short')
    response = client.post(
        make_short_point,
        json={
            'url': 'http://some_url',
            'creator_name': 'some_name',
            'users': 'all'
        }
    )
    assert response.status_code == 201
    assert response.json()['short_link'] != ''


def test_open_incorrect_url():
    response = client.get('/ldQmvl')
    assert response.status_code == 404


def test_ping_db():
    ping_db_point = app.url_path_for('ping_db')
    response = client.get(ping_db_point)

    assert response.json()['status_code'] == 200
    assert response.json()['body']['db_status'] == 'active'


def test_user_status():
    make_short_point = app.url_path_for('make_short')
    response = client.post(
        make_short_point,
        json={
            'url': 'http://some_url',
            'creator_name': 'some_name',
            'users': 'somebody'
        }
    )
    links_status_point = app.url_path_for('get_links_status')
    response = client.get(links_status_point)
    assert response.json()[0]['status_code'] == 200
    assert response.json()[0]['body']['short-url'] != ''
    assert response.json()[0]['body']['original-url'] == 'http://some_url'
    assert response.json()[0]['body']['type'] == 'private'
