"""Initial migration: create users and oauth_tokens tables

Revision ID: e1aecf0cfd51
Revises: 
Create Date: 2025-11-22 05:04:46.642421

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1aecf0cfd51'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建 users 和 oauth_tokens 表"""
    
    # 创建 users 表
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False, comment='用户名'),
        sa.Column('password_hash', sa.String(length=255), nullable=True, comment='密码哈希值'),
        sa.Column('oauth_id', sa.String(length=255), nullable=True, comment='OAuth 提供商的用户 ID'),
        sa.Column('avatar_url', sa.String(length=512), nullable=True, comment='用户头像 URL'),
        sa.Column('trust_level', sa.Integer(), nullable=False, server_default='0', comment='用户信任等级'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='账号是否激活'),
        sa.Column('is_silenced', sa.Boolean(), nullable=False, server_default='false', comment='是否被禁言'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='更新时间'),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True, comment='最后登录时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('oauth_id')
    )
    
    # 创建 users 表索引
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_oauth_id', 'users', ['oauth_id'])
    
    # 创建 oauth_tokens 表
    op.create_table(
        'oauth_tokens',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='关联的用户 ID'),
        sa.Column('access_token', sa.Text(), nullable=False, comment='OAuth 访问令牌'),
        sa.Column('refresh_token', sa.Text(), nullable=True, comment='OAuth 刷新令牌'),
        sa.Column('token_type', sa.String(length=50), nullable=False, server_default='bearer', comment='令牌类型'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False, comment='令牌过期时间'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='更新时间'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )


def downgrade() -> None:
    """删除 oauth_tokens 和 users 表"""
    op.drop_table('oauth_tokens')
    op.drop_index('ix_users_oauth_id', table_name='users')
    op.drop_index('ix_users_username', table_name='users')
    op.drop_table('users')
