"""
Модуль с корутинами,
выполняющими сложные действия.
"""

from random import choices

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update

from core import config
from core.config import PROJECT_HOST as HOST
from core.config import (logger, CHARACTERS, SHORT_URL_LENGTH)
from models.models import (LongShortUrl, UserPassword, UrlVisibility, UrlInfo)


async def create_short_url(url: str,
                           session: AsyncSession,
                           creator_name: str,
                           users_visibility: str = 'all') -> str:
    """
    Корутина, возвращающая короткий URL.
    В случае, если поданный URL, уже обрабатывался, возвращает
    соответсвующее значение из БД.
    Иначе генерирует новый короткий URL и добавляет в БД.
    Проверяет настройки видимости короткого URL.
    В случае первой обработки, если пользователь не указал ограничения,
    выставляется доступ all.
    В ином случае доступ выставляется только создателю
    и указанным пользователям.
    """
    check_existence_query = select(
        LongShortUrl.short_url).where(LongShortUrl.url == url)
    short_url_query_result = (await
                              session.execute(check_existence_query)).all()

    is_url_exist = short_url_query_result != []
    if is_url_exist:
        logger.info('>>>> OLD URL <<<<')
        short_url = short_url_query_result[0][0]
    else:
        logger.info('>>>> NEW URL <<<<')
        while True:
            short_url = ''.join(choices(CHARACTERS, k=SHORT_URL_LENGTH))
            check_uniq_short_url_query = select(LongShortUrl).where(
                LongShortUrl.short_url == short_url)
            check_uniq_query_result = (
                await session.execute(check_uniq_short_url_query)).all()

            if check_uniq_query_result == []:
                new_url_entry = LongShortUrl(url=url, short_url=short_url)
                session.add(new_url_entry)
                await session.commit()
                break

    url_visability_query = (
        select(UrlVisibility.users).
        where(UrlVisibility.url == url)
    )
    url_visability_query_result = (
        await session.execute(url_visability_query)
    ).all()

    logger.debug(url_visability_query_result)

    if url_visability_query_result == []:
        logger.debug('!!!!! NEW VISABILITY')
        if users_visibility == '':
            users_visibility = 'all'
        else:
            users_visibility = f'{creator_name} {users_visibility}'

        logger.debug(users_visibility)
        new_url_visability = UrlVisibility(url=url, users=users_visibility)
        session.add(new_url_visability)
        await session.commit()
    else:
        logger.debug('!!!!! UPDATE VISABILITY')
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

        url_visability_query = select(UrlVisibility).where(
            UrlVisibility.url == url)
        url_visability_query_result = (
            await session.execute(url_visability_query)).all()

    return short_url


async def find_link_to_redirect(
    short_url: str, session: AsyncSession
) -> str:
    """
    Корутина, возвращающая истинный url.
    """
    get_url_query = select(
        LongShortUrl.url).where(LongShortUrl.short_url == short_url)
    get_url_query_result = (await session.execute(get_url_query)).all()
    if get_url_query_result != []:
        url = get_url_query_result[0][0]
    else:
        url = f'{HOST}:{config.PROJECT_PORT}/path_error'
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
    print(username, password)
    if ' ' in username:
        return False

    check_password_query = select(
        UserPassword.password).where(UserPassword.username == username)
    check_password_query_result = (
        await session.execute(check_password_query)).all()

    print(f'true_password == {check_password_query_result}')
    if check_password_query_result == []:

        logger.info('>>>> NEW USER <<<<')
        new_user = UserPassword(username=username, password=password)
        session.add(new_user)
        await session.commit()
        return True

    else:
        logger.info('>>>> OLD USER <<<<')
        if password == check_password_query_result[0][0]:
            logger.info('>>>> LOG IN SUCCESS <<<<')

            return True
        else:
            logger.info('>>>> LOG IN FAIL <<<<')

            return False


async def check_access(
    username: str, password: str,
    session: AsyncSession
) -> bool:
    """
    Корутина для проверки прав доступа перехода по ссылке.
    """
    check_password_query = select(
        UserPassword.password).where(UserPassword.username == username)
    check_password_query_result = (
        await session.execute(check_password_query)).all()

    if check_password_query_result != []:
        logger.info('>>>> USER EXISTS <<<<')
        if password == check_password_query_result[0][0]:
            logger.info('>>>> check_access SUCCESS <<<<')

            return True
        else:
            logger.info('>>>> check_access FAIL <<<<')

            return False
    else:
        return False


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
    new_url_info = UrlInfo(short_url=short_url,
                           orig_url=orig_url,
                           url_id=url_id,
                           link_type=vis)

    session.add(new_url_info)
    await session.commit()


async def get_cnt_action_with_link(short_url: str,
                                   session: AsyncSession) -> int:
    """
    Корутина для подсчета количества переходов по ссылке.
    """
    get_url_info_query = select(UrlInfo).where(UrlInfo.short_url == short_url)
    get_url_info_query_result = (await
                                 session.execute(get_url_info_query)).all()
    return len(get_url_info_query_result)
