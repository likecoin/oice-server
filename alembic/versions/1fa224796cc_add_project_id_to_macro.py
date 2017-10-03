"""add project id to macro

Revision ID: 1fa224796cc
Revises: 1a31ac19a27
Create Date: 2015-07-15 19:58:32.652485

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1fa224796cc'
down_revision = '1a31ac19a27'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'macro', sa.Column(
            'project_id', sa.Integer,
            sa.ForeignKey('project.id', ondelete='CASCADE')))

    # Set all existing macro to the first project
    conn = op.get_bind()
    conn.execute("""
        UPDATE macro SET project_id = (SELECT id FROM project LIMIT 1);""")


def downgrade():
    op.drop_constraint(
        'macro_ibfk_1', table_name='macro', type_="foreignkey")
    op.drop_column('macro', 'project_id')
