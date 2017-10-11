"""use long text for import result

Revision ID: 20e556d0e1a
Revises: 14eb4c07256
Create Date: 2015-05-26 15:38:45.175390

"""

# revision identifiers, used by Alembic.
revision = '20e556d0e1a'
down_revision = '14eb4c07256'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_column('project_import', 'result')
    op.add_column('project_import',
        sa.Column('result', sa.Text(length=2**31), nullable=False, default="")
    )

def downgrade():
    op.drop_column('project_import', 'result')
    op.add_column('project_import',
        sa.Column('result', sa.Text, nullable=False, default="")
    )
