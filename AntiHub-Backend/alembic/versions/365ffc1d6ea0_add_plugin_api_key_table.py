"""add_plugin_api_key_table

Revision ID: 365ffc1d6ea0
Revises: e1aecf0cfd51
Create Date: 2025-11-22 06:07:37.169677

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '365ffc1d6ea0'
down_revision: Union[str, None] = 'e1aecf0cfd51'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建 plugin_api_keys 表
    op.create_table(
        'plugin_api_keys',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('api_key', sa.Text(), nullable=False, comment='用户的plug-in API密钥（加密存储）'),
        sa.Column('plugin_user_id', sa.String(length=255), nullable=True, comment='plug-in-api系统中的用户ID'),
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='密钥是否激活'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='更新时间'),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True, comment='最后使用时间'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建索引
    op.create_index(op.f('ix_plugin_api_keys_user_id'), 'plugin_api_keys', ['user_id'], unique=True)


def downgrade() -> None:
    # 删除索引
    op.drop_index(op.f('ix_plugin_api_keys_user_id'), table_name='plugin_api_keys')
    
    # 删除表
    op.drop_table('plugin_api_keys')
