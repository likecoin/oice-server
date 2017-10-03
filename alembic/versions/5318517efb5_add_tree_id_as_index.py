"""add tree id as index

Revision ID: 5318517efb5
Revises: 306a7cdb6d
Create Date: 2015-05-29 16:23:58.295498

"""

# revision identifiers, used by Alembic.
revision = '5318517efb5'
down_revision = '306a7cdb6d'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_index('tree_id_idx', 'tag', ['tree_id'])


def downgrade():
    op.drop_index('tree_id_idx', table_name='tag')