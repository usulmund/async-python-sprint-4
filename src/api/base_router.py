"""
Модуль с подключением роутеров.
"""
from fastapi import APIRouter

from .routers.admin_router import admin_router
from .routers.app_router import app_router

router = APIRouter()
router.include_router(admin_router, tags=['admin'])
router.include_router(app_router, tags=['app'])
