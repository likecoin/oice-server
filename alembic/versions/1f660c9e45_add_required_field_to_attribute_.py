"""add required field to Attribute_definition

Revision ID: 1f660c9e45
Revises: 53bc4b74f98
Create Date: 2015-04-24 15:46:25.332574

"""

# revision identifiers, used by Alembic.
revision = '1f660c9e45'
down_revision = '53bc4b74f98'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('attribute_definition',
        sa.Column('required', sa.Boolean)
    )

def downgrade():
    op.drop_column('attribute_definition', 'required')
