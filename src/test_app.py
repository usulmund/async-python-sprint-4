"""
Модуль с тестами.
"""

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_root():
    response = client.get('/')
    assert response.status_code == 200


def test_auth():
    response = client.post(
        '/auth',
        json={
            'username': 'some_name',
            'password': 'some_password'
        }
    )
    assert response.status_code == 200
    assert response.json() == {'message': 'Welcome, some_name!'}


def test_url_shorter():
    response = client.post(
        '/short',
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
    response = client.get('/ping')
    assert response.status_code == 200
    assert response.json()['db_status'] == 'active'


def test_user_status():
    response = client.post(
        '/short',
        json={
            'url': 'http://some_url',
            'creator_name': 'some_name',
            'users': 'somebody'
        }
    )
    response = client.get('/user/status')
    assert response.status_code == 200
    assert response.json()[0]['short-url'] != ''
    assert response.json()[0]['original-url'] == 'http://some_url'
    assert response.json()[0]['type'] == 'private'
