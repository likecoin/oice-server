"""rename extra_files to base_zip

Revision ID: 52232e78f1f
Revises: 1ec87c6930f
Create Date: 2015-07-02 23:49:41.998064

"""

# revision identifiers, used by Alembic.
revision = '52232e78f1f'
down_revision = '1ec87c6930f'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('project', 'extra_files', new_column_name='base_zip', existing_type=sa.Unicode(1024))


def downgrade():
    op.alter_column('project', 'base_zip', new_column_name='extra_files', existing_type=sa.Unicode(1024))
