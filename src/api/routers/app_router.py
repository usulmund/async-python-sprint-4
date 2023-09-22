"""
Модуль с описанием точек входа,
связанный с обработкой ссылок.
Привязаны к объекту app_router.
"""

from fastapi import APIRouter, Depends, Body
from fastapi.responses import (
    ORJSONResponse,
    FileResponse,
    RedirectResponse,
    HTMLResponse
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core import config
from core.config import logger
from models.models import UrlVisibility
from db.db import get_session

from services.logic import (
    create_short_url,
    find_link_to_redirect,
    check_auth,
    check_access,
    add_info,
)

from core.config import PROJECT_HOST as HOST, NO_PAGE_HTML

app_router = APIRouter()


@app_router.get('/')
async def get_user_data() -> FileResponse:
    """
    Корутина для перенаправления на форму аутентификации.
    """
    return FileResponse('api/auth_form.html')


@app_router.post('/auth')
async def check_auth_data_to_log_in(
        data=Body(),
        session: AsyncSession = Depends(get_session)
) -> ORJSONResponse:
    """
    Корутина для проверки логина и пароля, получаемых
    из формы в api/auth_form.html.
    В случае успешной авторизации пользователю становится
    доступна кнопка для преобразования URL.
    Вызывается по кнопке Log in.
    """
    username = data['username']
    password = data['password']
    logger.debug(f'!!!!!!auth {username} -- {password}')

    while True:
        is_auth_success = await check_auth(username, password, session)

        if is_auth_success:
            return ORJSONResponse({'message': f'Welcome, {username}!'},
                                  status_code=200)
        else:
            return ORJSONResponse(
                {'message': 'Username or password is incorrect.'},
                status_code=401)


@app_router.post('/short')
async def make_short(
        data=Body(),
        session: AsyncSession = Depends(get_session)
) -> ORJSONResponse:
    """
    Корутина для преобразования URL.
    Вызывается по кнопке Generate link.
    """
    url = data['url']
    creator_name = data['creator_name']
    users_visibility = data['users']

    short_url = await create_short_url(url, session, creator_name,
                                       users_visibility)
    return ORJSONResponse(
        {'short_link': f'{HOST}:{config.PROJECT_PORT}/{short_url}'},
        status_code=201)


@app_router.post('/private_link')
async def check_auth_data(
        data=Body(),
        session: AsyncSession = Depends(get_session)
) -> ORJSONResponse:
    """
    Корутина для проверки логина и пароля пользователя
    при попытке перейти по приватной ссылке.
    """
    username = data['username']
    password = data['password']

    is_auth_success = await check_access(username, password, session)

    if is_auth_success:
        return ORJSONResponse({'message': f'Welcome, {username}!'},
                              status_code=200)
    else:
        return ORJSONResponse(
            {'message': 'Username or password is incorrect.'}, status_code=401)


@app_router.get('/{short_url}')
async def action_handler(
        short_url: str,
        session: AsyncSession = Depends(get_session)
) -> RedirectResponse | HTMLResponse:
    logger.info(f'~~~ short url: {short_url} ~~~~')
    # localhost:8000/Gm9yqR
    try:
        await add_info(short_url, session)
    except IndexError:
        logger.warning('PAGE NOT FOUND')
    url = await find_link_to_redirect(short_url, session)

    url_visability_query = (select(
        UrlVisibility.users).where(UrlVisibility.url == url))
    try:
        url_visability_query_result = (
            await session.execute(url_visability_query)).all()[0][0]
        logger.debug('CAN WATCH!!!! ', url_visability_query_result)
        if 'all' in url_visability_query_result:  # проверить точно ли ок
            return RedirectResponse(url, status_code=307)
        else:
            with open('api/private_link.html', 'r') as html_file:
                html_content = html_file.read().replace('<PRIVATE_URL>', url)
            return HTMLResponse(content=html_content, status_code=200)
    except IndexError:
        logger.warning('PAGE NOT FOUND')
        return HTMLResponse(content=NO_PAGE_HTML, status_code=404)
