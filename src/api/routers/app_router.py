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

from core import config
from core.config import logger
from db.db import get_session
from schemas.response_models import JsonEntity
from services.logic import (
    create_short_url,
    find_link_to_redirect,
    check_auth,
    check_access,
    add_info,
    redirect_to_orig_link,
)

from core.config import PROJECT_HOST as HOST

app_router = APIRouter()


@app_router.get('/')
async def get_user_data() -> FileResponse:
    """
    Корутина для перенаправления на форму аутентификации.
    """
    return FileResponse('templates/auth_form.html')


@app_router.post('/auth', response_model=JsonEntity)
async def check_auth_data_to_log_in(
        data=Body(),
        session: AsyncSession = Depends(get_session)
) -> ORJSONResponse:
    """
    Корутина для проверки логина и пароля, получаемых
    из формы в templates/auth_form.html.
    В случае успешной авторизации пользователю становится
    доступна кнопка для преобразования URL.
    Вызывается по кнопке Log in.
    """
    username = data['username']
    password = data['password']
    logger.debug(f'auth {username} -- {password}')

    is_auth_success = await check_auth(username, password, session)

    if is_auth_success:
        return ORJSONResponse(
            {'message': f'Welcome, {username}!'},
            status_code=200
        )
    else:
        return ORJSONResponse(
            {'message': 'Username or password is incorrect.'},
            status_code=401)


@app_router.post('/short', response_model=JsonEntity)
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

    short_url = await create_short_url(
        url=url,
        session=session,
        creator_name=creator_name,
        users_visibility=users_visibility
    )
    return ORJSONResponse(
        {'short_link': f'{HOST}:{config.PROJECT_PORT}/{short_url}'},
        status_code=201)


@app_router.post('/private_link', response_model=JsonEntity)
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
    """
    Корутина, для перехвата коротких ссылок.
    Проверяет существование ссылки и перенаправляет
    на оригинальный адрес.
    """
    logger.info(f'~~~ short url: {short_url} ~~~~')
    try:
        await add_info(short_url, session)
    except IndexError:
        logger.warning('PAGE NOT FOUND')
    url = await find_link_to_redirect(short_url, session)
    return (await redirect_to_orig_link(url, session))
