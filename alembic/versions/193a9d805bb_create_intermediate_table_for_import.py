"""Create intermediate table for import

Revision ID: 193a9d805bb
Revises: 53be2a24f3
Create Date: 2015-05-20 14:17:26.220994

"""

# revision identifiers, used by Alembic.
revision = '193a9d805bb'
down_revision = '53be2a24f3'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'project_import',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('project_id', sa.Integer,
            sa.ForeignKey('project.id'), nullable=False),
        sa.Column('source_files', sa.Unicode(1024), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        mysql_engine='InnoDB'
    )


def downgrade():
    op.drop_table('project_import')
