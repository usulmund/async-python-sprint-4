"""
Модуль с корутинами,
cодержащами основную бизнес-логику
c обработкой данных и взаимодействием
с БД.
"""

from random import choices

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from sqlalchemy.sql.expression import exists, func
from fastapi.responses import (
    RedirectResponse,
    HTMLResponse
)

from core.config import (
    PROJECT_HOST as HOST,
    PROJECT_PORT as PORT,
    NO_PAGE_HTML,
    logger,
    CHARACTERS,
    SHORT_URL_LENGTH,
)
from models.models import LongShortUrl, UserPassword, UrlVisibility, UrlInfo


async def create_short_url(
    url: str,
    session: AsyncSession,
    creator_name: str,
    users_visibility: str = 'all'
) -> str:
    """
    Корутина, возвращающая короткий URL.
    Создает либо берет из базы данных и
    обрабатывает.
    """
    check_existence_query = (
        select(LongShortUrl.short_url).
        where(LongShortUrl.url == url)
    )
    short_url_query_result = (await
                              session.execute(check_existence_query)).all()

    short_url = await get_or_generate_short_url(
        url=url,
        short_url_query_result=short_url_query_result,
        session=session
    )
    await handle_visability(url, creator_name, users_visibility, session)

    return short_url


async def get_or_generate_short_url(
    url: str,
    short_url_query_result: list[tuple],
    session: AsyncSession
) -> str:
    """
    Корутина, которая в зависимости от
    существования короткой ссылки либо
    создает новую,
    либо возвращает существующую из базы
    данных.
    """
    is_url_exist = short_url_query_result != []
    if is_url_exist:
        logger.info('>>>> OLD URL <<<<')
        short_url = short_url_query_result[0][0]
    else:
        logger.info('>>>> NEW URL <<<<')
        is_generate_success = False
        while not is_generate_success:
            short_url = ''.join(choices(CHARACTERS, k=SHORT_URL_LENGTH))

            new_url_entry = LongShortUrl(url=url, short_url=short_url)
            session.add(new_url_entry)
            try:
                await session.commit()
                is_generate_success = True
            except Exception as e:
                is_generate_success = False
                await session.rollback()
                logger.warning(f'Try to paste dub of short url: {e}')

    return short_url


async def handle_visability(
        url: str,
        creator_name: str,
        users_visibility: str,
        session: AsyncSession
) -> None:
    """
    Корутина, обрабатывающая состояние
    видимости ссылки в зависимости от того,
    создана ли ссылка только что или
    уже существует.
    """
    url_visability_query = (
        select(UrlVisibility.users).
        where(UrlVisibility.url == url)
    )
    url_visability_query_result = (
        await session.execute(url_visability_query)
    ).all()

    logger.debug(url_visability_query_result)

    if url_visability_query_result == []:
        await create_new_visability(
            creator_name,
            url,
            users_visibility,
            session
        )

    else:
        await update_visability(
            creator_name,
            url,
            users_visibility,
            url_visability_query_result,
            session
        )


async def create_new_visability(
        creator_name: str,
        url: str,
        users_visibility: str,
        session: AsyncSession
) -> None:
    """
    Корутина, создающая запись о
    состоянии видимости ссылки для
    других пользователей.
    Вызывается при первоначальном создании
    короткой ссылки.
    """
    logger.debug('NEW VISABILITY')
    if users_visibility == '':
        users_visibility = 'all'
    else:
        users_visibility = f'{creator_name} {users_visibility}'

    logger.debug(users_visibility)
    new_url_visability = UrlVisibility(url=url, users=users_visibility)
    session.add(new_url_visability)
    await session.commit()


async def update_visability(
        creator_name: str,
        url: str,
        users_visibility: str,
        url_visability_query_result: list,
        session: AsyncSession
) -> None:
    """
    Корутина, обрабатывающая запрос
    пользователя на изменения видимости
    короткой ссылки.
    Новые права на видимость сохраняются
    в базе данных.
    """
    logger.debug('UPDATE VISABILITY')
    users_visibility = await create_visability_str(
        creator_name,
        users_visibility,
        url_visability_query_result
    )
    update_query = (
        update(UrlVisibility).
        where(UrlVisibility.url == url).values(
            {
                'url': url,
                'users': users_visibility
            }
        )
    )
    await session.execute(update_query)
    await session.commit()


async def create_visability_str(
        creator_name: str,
        users_visibility: str,
        url_visability_query_result: list,
) -> str:
    """
    Корутина, формирующая новую строку
    с именами пользователей, которым доступна
    короткая ссылка.
    """
    users_set = set(
        url_visability_query_result[0][0].
        split(' ')
    )
    is_have_all_before = 'all' in users_set
    is_have_all_after = False
    is_have_not_none = False
    for user in users_visibility.split(' '):
        if user == 'all':
            is_have_all_after = True
        if user != '':
            is_have_not_none = True
            users_set.add(user)
    users_set.add(creator_name)

    if is_have_all_before and not is_have_all_after and is_have_not_none:
        users_set.remove('all')

    logger.debug(users_set)
    users_visibility = ' '.join(users_set)
    return users_visibility


async def find_link_to_redirect(
    short_url: str, session: AsyncSession
) -> str:
    """
    Корутина, возвращающая истинный url
    в соответствии с сокращенным
    из базы данных.
    """
    get_url_query = select(
        LongShortUrl.url).where(LongShortUrl.short_url == short_url)
    get_url_query_result = (await session.execute(get_url_query)).all()
    if get_url_query_result != []:
        url = get_url_query_result[0][0]
    else:
        url = f'{HOST}:{PORT}/path_error'
    logger.debug(f'true url: {url}')
    return url


async def check_auth(
    username: str, password: str,
    session: AsyncSession
) -> bool:
    """
    Корутинка для проверки данных пользователя.
    При создании аккаунта возможно использовать
    логин только без пробелов.
    Возвращает True в случае корректных данных.
    """
    if ' ' in username:
        return False

    is_log_in_success = False
    new_user = UserPassword(username=username, password=password)
    session.add(new_user)
    try:
        is_log_in_success = True
        await session.commit()

    except Exception:
        logger.info('USER IS EXIST')
        await session.rollback()

        check_password_query = select(
            UserPassword.password).where(UserPassword.username == username)
        check_password_query_result = (
            await session.execute(check_password_query)).all()

        logger.info(f'true_password == {check_password_query_result}')

        if password == check_password_query_result[0][0]:
            logger.info('>>>> LOG IN SUCCESS <<<<')
            is_log_in_success = True
        else:
            logger.info('>>>> LOG IN FAIL <<<<')
            is_log_in_success = False

    return is_log_in_success


async def check_access(
    username: str, password: str,
    session: AsyncSession
) -> bool:
    """
    Корутина для проверки прав доступа перехода по ссылке.
    """
    check_user_query = (
        select(UserPassword).where(
            UserPassword.username == username,
            UserPassword.password == password
        )
    )

    is_have_access = (
        await session.execute(exists(check_user_query).select())
    ).all()[0][0]

    return is_have_access


async def add_info(short_url: str, session: AsyncSession) -> None:
    """
    Корутина для добавления информации о взаимодейсвии с ссылкой.
    """
    get_orig_url_query = select(
        LongShortUrl.url,
        LongShortUrl.id,
    ).where(LongShortUrl.short_url == short_url)

    get_orig_url_query_result = (
        await session.execute(get_orig_url_query)
    ).all()

    orig_url = get_orig_url_query_result[0][0]
    url_id = get_orig_url_query_result[0][1]

    get_visability_query = select(
        UrlVisibility.users).where(UrlVisibility.url == orig_url)
    get_visability_query_result = (
        await session.execute(get_visability_query)).all()[0][0]

    if 'all' in get_visability_query_result:
        vis = 'public'
    else:
        vis = 'private'

    new_url_info = UrlInfo(
        short_url=short_url,
        orig_url=orig_url,
        url_id=url_id,
        link_type=vis
    )

    session.add(new_url_info)
    await session.commit()


async def get_cnt_action_with_link(
    short_url: str,
    session: AsyncSession
) -> int:
    """
    Корутина для подсчета количества переходов по ссылке.
    """
    get_url_info_query = (
        select(func.count(UrlInfo.short_url)).
        group_by(UrlInfo.short_url).
        having(UrlInfo.short_url == short_url)
    )
    cnt = (await session.execute(get_url_info_query)).scalar()

    return cnt


async def redirect_to_orig_link(
        url: str,
        session: AsyncSession
) -> RedirectResponse | HTMLResponse:
    """
    Корутина, обрабатывающая перенаправление на
    оригинальный адрес.
    Проверяет существование такого в базе данных,
    а также проверяет тип доступности для пользователей.
    """
    url_visability_query = (select(
        UrlVisibility.users).where(UrlVisibility.url == url))
    try:
        url_visability_query_result = (
            await session.execute(url_visability_query)).all()[0][0]
        if 'all' in url_visability_query_result:
            return RedirectResponse(url, status_code=307)
        else:
            with open('templates/private_link.html', 'r') as html_file:
                html_content = html_file.read().replace('<PRIVATE_URL>', url)
            return HTMLResponse(content=html_content, status_code=200)
    except IndexError:
        logger.warning('PAGE NOT FOUND')
        return HTMLResponse(content=NO_PAGE_HTML, status_code=404)
