"""set avatar_storage to Nullable

Revision ID: 236744c1007
Revises: 501bbe9029f
Create Date: 2016-11-25 15:26:50.726637

"""

# revision identifiers, used by Alembic.
revision = '236744c1007'
down_revision = '501bbe9029f'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    op.alter_column('user', 'avatar_storage',
               existing_type=mysql.VARCHAR(length=255),
               nullable=True,
               existing_server_default=None)
    conn = op.get_bind()
    conn.execute("""
        UPDATE `user`
        SET `avatar_storage` = NULL
        WHERE `avatar_storage` = '{"filename": "", "storage": "fs", "size": 0, "path": ""}'
    """)


def downgrade():
    conn = op.get_bind()
    conn.execute("""
        UPDATE `user`
        SET `avatar_storage` = '{"filename": "", "storage": "fs", "size": 0, "path": ""}'
        WHERE `avatar_storage` = NULL
    """)
    op.alter_column('user', 'avatar_storage',
               existing_type=mysql.VARCHAR(length=255),
               nullable=False,
               existing_server_default=sa.text('\'{"filename": "", "storage": "fs", "size": 0, "path": ""}\''))
