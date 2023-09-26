"""
Модуль с описанием точек входа,
связанный с получением данных
о состоянии приложения.
Привязаны к объекту admin_router.
"""

from typing import Optional, Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql.expression import exists

from models.models import (
    UrlVisibility,
    LongShortUrl,
    UrlInfo,
    UserPassword
)
from schemas.response_models import JsonEntity
from db.db import get_session
from services.logic import get_cnt_action_with_link
from core.config import (
    PROJECT_HOST as HOST,
    PROJECT_PORT as PORT,
    PAGINATOR_OFFSET,
    PAGINATOR_LIMIT,
    logger,
)

admin_router = APIRouter()


async def paginator_response():
    """
    Корунтина для использования в качестве DI,
    задающая пагинацию возвращаемых данных.
    """
    return {
        "offset": PAGINATOR_OFFSET,
        "limit": PAGINATOR_LIMIT
    }


@admin_router.get('/ping', response_model=JsonEntity)
async def ping_db(
        session: AsyncSession = Depends(get_session)
) -> JsonEntity:
    """
    Корутина для проверки доступности базы данных.
    Опрашивает существующую таблицы, собирает
    информацию о количестве доступных записей.
    В случае ошибки заполняется поле db_status
    значением inactive.
    """
    result = dict()
    result['db_status'] = 'active'
    status_code = 200
    for model in [LongShortUrl, UserPassword, UrlVisibility, UrlInfo]:
        try:
            check_long_short_url_query = select(model)
            check_long_short_url_query_result = (
                await session.execute(check_long_short_url_query)).all()
            records_cnt = len(check_long_short_url_query_result)
            result[model.__tablename__] = f'{records_cnt} records'

        except Exception as e:
            logger.error(f'CONNECT ERROR TO DB: {e}')
            result[model.__tablename__] = 'connection error'
            result['db_status'] = 'inactive'
            status_code = 503

    return JsonEntity(body=result, status_code=status_code)


@admin_router.get('/user/status', response_model=list[JsonEntity])
async def get_links_status(
        session: AsyncSession = Depends(get_session),
        params: dict = Depends(paginator_response),
) -> list[JsonEntity]:
    """
    Корутина для проверки статусов.
    Возвращает список из словарей с полями
    short-id, short-url, original-url, type
    в соответствие с содержимым БД.
    """
    create_response_query = (select(
        LongShortUrl,
        UrlVisibility).filter(LongShortUrl.url == UrlVisibility.url))
    offset = params['offset']
    limit = params['limit']
    create_response_query_result = (
        await session.execute(create_response_query)).all()
    response = []
    last_record_ind = min(limit + offset, len(create_response_query_result))

    for i in range(offset, last_record_ind):
        row = create_response_query_result[i]
        record = dict()
        record['short-id'] = row[0].id
        record['short-url'] = f'http://{HOST}:{PORT}/{row[0].short_url}'
        record['original-url'] = row[0].url
        if 'all' in row[1].users:
            record['type'] = 'public'
        else:
            record['type'] = 'private'

        response.append(JsonEntity(body=record))

    return response


@admin_router.get('/{short_url}/status', response_model=JsonEntity | list[Any])
async def get_short_url_statistics(
        short_url: str,
        full_info: Optional[bool] = False,
        limit: Optional[int] = PAGINATOR_LIMIT,
        offset: Optional[int] = PAGINATOR_OFFSET,
        session: AsyncSession = Depends(get_session)
) -> JsonEntity | list[Any]:
    """
    Корутина для получения статистики переходов.
    При использовании без параметров возвращает количество
    переходов по указанной ссылке.
    Если параметры указаны, список со всеми взаимодейтсвиями
    с указанной ссылкой.
    Пример: bmywdm/status?full_info=True&limit=10&offset=1
    """
    check_url_query = (
        select(UrlInfo).where(
            UrlInfo.short_url == short_url
        )
    )

    is_url_exist = (
        await session.execute(exists(check_url_query).select())
    ).all()[0][0]
    if not is_url_exist:
        return JsonEntity(
            body={
                'url': short_url,
                'error': 'Not found',
            },
            status_code=404
        )

    if full_info:
        get_info_query = select(UrlInfo)
        get_info_query_result = (await session.execute(get_info_query)).all()
        logger.info('full info')
        if not offset:
            offset = PAGINATOR_OFFSET
        if not limit:
            limit = PAGINATOR_LIMIT

        last_record_ind = min(limit + offset, len(get_info_query_result))
        records_to_show = [
            get_info_query_result[i] for i in range(offset, last_record_ind)
        ]
        return records_to_show
    else:
        logger.info('action cnt')
        action_cnt = await get_cnt_action_with_link(short_url, session)
        return JsonEntity(
            body={
                'url': f'{HOST}:{PORT}/{short_url}',
                'count of transitions': str(action_cnt)
            }
        )
