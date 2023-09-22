"""
Модуль с описанием основных настроек.
"""
import os
import logging
from logging import config as logging_config
from pydantic import BaseSettings

from core.logger import LOGGING

logging_config.dictConfig(LOGGING)
logger = logging.getLogger()

PROJECT_NAME = os.getenv('PROJECT_NAME', 'UrlShorter')
PROJECT_HOST = os.getenv('PROJECT_HOST', 'localhost')
PROJECT_PORT = int(os.getenv('PROJECT_PORT', '8080'))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CHARACTERS = 'ABCDEFGHJKLMNOPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz234567890'
SHORT_URL_LENGTH = 6

PAGINATOR_OFFSET = 0
PAGINATOR_LIMIT = 10

NO_PAGE_HTML = """
    <html>
        <head>
            <title>Error</title>
        </head>
        <body>
            <h1>No such page</h1>
        </body>
    </html>
"""


class AppSettings(BaseSettings):
    app_title: str = 'UrlShorter'
    database_dsn: str = ''

    class Config:
        env_file = '.env'


app_settings = AppSettings()
