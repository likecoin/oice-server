"""add ks_id column in project_export table

Revision ID: 566d9896854
Revises: 1b1772327d3
Create Date: 2015-08-10 15:48:24.859950

"""

# revision identifiers, used by Alembic.
revision = '566d9896854'
down_revision = '1b1772327d3'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('project_export',
                  sa.Column('ks_id', sa.Integer, sa.ForeignKey('ks.id')))


def downgrade():
    op.drop_column('project_export', 'ks_id')
