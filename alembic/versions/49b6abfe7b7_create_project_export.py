"""create project_export

Revision ID: 49b6abfe7b7
Revises: 20e556d0e1a
Create Date: 2015-05-26 18:51:40.309373

"""

# revision identifiers, used by Alembic.
revision = '49b6abfe7b7'
down_revision = '20e556d0e1a'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'project_export',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('project_id', sa.Integer,
            sa.ForeignKey('project.id'), nullable=False),
        sa.Column('exported_files', sa.Unicode(1024), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        mysql_engine='InnoDB'
    )


def downgrade():
    op.drop_table('project_export')
