"""empty message

Revision ID: d0d40367ddd5
Revises:
Create Date: 2023-09-26 15:31:37.003300

"""
from typing import Sequence, Union
from datetime import datetime

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd0d40367ddd5'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'long_short_url',
        sa.Column(
            'id',
            sa.Integer,
            primary_key=True
        ),
        sa.Column(
            'url',
            sa.String(200),
            unique=True,
            nullable=False
        ),
        sa.Column(
            'short_url',
            sa.String(50),
            unique=True,
            nullable=False
        ),
        sa.Column(
            'created_at',
            sa.DateTime,
            index=True,
            default=datetime.utcnow
        ),
    )
    op.create_table(
        'user_password',
        sa.Column(
            'id',
            sa.Integer,
            primary_key=True
        ),
        sa.Column(
            'username',
            sa.String(100),
            unique=True,
            nullable=False
        ),
        sa.Column(
            'password',
            sa.String(50),
            nullable=False
        ),
        sa.Column(
            'created_at',
            sa.DateTime,
            index=True,
            default=datetime.utcnow
        ),
    )

    op.create_table(
        'url_visibility',
        sa.Column(
            'url',
            sa.String(200),
            primary_key=True
        ),
        sa.Column(
            'users',
            sa.String(500),
            nullable=False
        ),
    )

    op.create_table(
        'url_info',
        sa.Column(
            'action_id',
            sa.Integer,
            primary_key=True
        ),
        sa.Column(
            'short_url',
            sa.String(100),
            nullable=False
        ),
        sa.Column(
            'orig_url',
            sa.String(200),
            nullable=False
        ),
        sa.Column(
            'url_id',
            sa.Integer
        ),
        sa.Column(
            'link_type',
            sa.String(10),
            nullable=False
        ),
        sa.Column(
            'action_time',
            sa.DateTime,
            index=True,
            default=datetime.utcnow
        ),
    )


def downgrade() -> None:
    op.drop_table('long_short_url')
    op.drop_table('user_password')
    op.drop_table('url_visibility')
    op.drop_table('url_info')
