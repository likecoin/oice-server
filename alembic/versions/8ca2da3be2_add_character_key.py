"""add character key

Revision ID: 8ca2da3be2
Revises: 3f1fa101441
Create Date: 2015-09-04 15:04:59.821544

"""

# revision identifiers, used by Alembic.
revision = '8ca2da3be2'
down_revision = 'fc43712814'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        'character',
        sa.Column('key', sa.Unicode(128), nullable=False))
    op.create_unique_constraint('uq_project_id_key', 'character', ['project_id', 'key'])


def downgrade():
    op.drop_column('character', 'key')
