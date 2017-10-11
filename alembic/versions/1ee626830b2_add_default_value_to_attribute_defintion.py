"""Add default_value to attribute defintion

Revision ID: 1ee626830b2
Revises: f939c65337
Create Date: 2015-05-19 12:01:13.796935

"""

# revision identifiers, used by Alembic.
revision = '1ee626830b2'
down_revision = 'f939c65337'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('attribute_definition',
        sa.Column('default_value', sa.Unicode(1024), nullable=True, default="")
    )

def downgrade():
    op.drop_column('attribute_definition', 'default_value')
