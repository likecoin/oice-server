"""add is deleted to project

Revision ID: 515440ba894
Revises: 1fa224796cc
Create Date: 2015-08-02 22:04:28.598890

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '515440ba894'
down_revision = '1fa224796cc'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'project', sa.Column('is_deleted', sa.Boolean, server_default='0')
    )


def downgrade():
    op.drop_column('project', 'is_deleted')
