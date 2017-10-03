"""add project id to asset

Revision ID: 1a31ac19a27
Revises: 49c717a61fb
Create Date: 2015-07-10 12:04:36.887772

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1a31ac19a27'
down_revision = '49c717a61fb'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'asset', sa.Column(
            'project_id', sa.Integer,
            sa.ForeignKey('project.id', ondelete='CASCADE')))

    # Set all existing asset to the first project
    conn = op.get_bind()
    conn.execute("""
        UPDATE asset SET project_id = (SELECT id FROM project LIMIT 1);""")


def downgrade():
    op.drop_constraint(
        'asset_ibfk_1', table_name='asset', type_="foreignkey")
    op.drop_column('asset', 'project_id')
