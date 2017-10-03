"""add result to project_import

Revision ID: 14eb4c07256
Revises: 193a9d805bb
Create Date: 2015-05-22 19:37:11.716794

"""

# revision identifiers, used by Alembic.
revision = '14eb4c07256'
down_revision = '193a9d805bb'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('project_import',
        sa.Column('result', sa.Text, nullable=False, default="")
    )

def downgrade():
    op.drop_column('project_import', 'result')
