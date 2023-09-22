"""
Модуль с описанием моделей БД.
"""
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from .base import Base


class LongShortUrl(Base):
    """
    Модель, хранящая связь настоящиx и укороченных URL.
    """
    __tablename__ = 'long_short_url'
    id = Column(Integer, primary_key=True)
    url = Column(String(200), unique=True, nullable=False)
    short_url = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime, index=True, default=datetime.utcnow)
    __mapper_args__ = {"eager_defaults": True}

    def __repr__(self):
        return "Url(id='%s', true='%s', short='%s')" % (
            self.id,
            self.url,
            self.short_url,
        )


class UserPassword(Base):
    """
    Модель, хранящая данные о пользователях.
    """
    __tablename__ = 'user_password'
    id = Column(Integer, primary_key=True)
    username = Column(
        String(100),
        unique=True,
        nullable=False
    )
    password = Column(String(50), nullable=False)
    created_at = Column(DateTime, index=True, default=datetime.utcnow)
    __mapper_args__ = {"eager_defaults": True}

    def __repr__(self):
        return "UserPassword(id='%s', username='%s', password='%s')" % (
            self.id,
            self.username,
            self.password,
        )


# пользователь будет вводить юзернэйм
class UrlVisibility(Base):
    """
    Модель, хранящая информацию,
    какие ссылки могут использоваться
    какими пользователями.
    """
    __tablename__ = 'url_visibility'
    url = Column(String(200), primary_key=True)
    users = Column(String(500), nullable=False)  # all or username + other
    # password = Column(String(50), nullable=False)
    # created_at = Column(DateTime, index=True, default=datetime.utcnow)
    __mapper_args__ = {"eager_defaults": True}

    def __repr__(self):
        return "UrlVisibility(url='%s', username='%s')" % (
            self.url,
            self.users,
        )


class UrlInfo(Base):
    """
    Модель, хранящая все переходы по ссылкам.
    """
    __tablename__ = 'url_info'
    action_id = Column(Integer, primary_key=True)
    short_url = Column(String(100), nullable=False)
    orig_url = Column(String(200), nullable=False)
    url_id = Column(Integer)
    link_type = Column(String(10), nullable=False)
    action_time = Column(DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return "UrlInfo(action_id='%s', short_url='%s')" % (
            self.action_id,
            self.short_url,
        )
