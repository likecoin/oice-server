"""Add character table

Revision ID: 306a7cdb6d
Revises: 49b6abfe7b7
Create Date: 2015-05-28 16:35:12.963074

"""

# revision identifiers, used by Alembic.
revision = '306a7cdb6d'
down_revision = '49b6abfe7b7'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'character',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('name', sa.Unicode(1024), nullable=False),
        sa.Column('macro_id', sa.Integer, sa.ForeignKey('macro.id'), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        mysql_engine='InnoDB'
    )


def downgrade():
    op.drop_table('character')
