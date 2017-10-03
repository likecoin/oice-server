"""Add project sub project

Revision ID: 49c717a61fb
Revises: 52232e78f1f
Create Date: 2015-07-09 17:39:30.999883

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '49c717a61fb'
down_revision = '52232e78f1f'
branch_labels = None
depends_on = None


def upgrade():

    op.create_table(
        'project_lib_project',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column(
            'project_id', sa.Integer,
            sa.ForeignKey('project.id', ondelete='CASCADE'), nullable=False),
        sa.Column(
            'lib_project_id', sa.Integer,
            sa.ForeignKey('project.id', ondelete='CASCADE'), nullable=False),
        mysql_engine='InnoDB'
    )

    op.add_column('project', sa.Column(
        'is_default_lib_project', sa.Boolean, server_default="0"))
    op.add_column('project', sa.Column(
        'is_lib_project', sa.Boolean, server_default="0"))

    # Add project itself to its sub projects list
    conn = op.get_bind()
    conn.execute("""
        INSERT INTO project_lib_project (project_id, lib_project_id)\
        SELECT id, id FROM project;""")


def downgrade():
    op.drop_table('project_lib_project')
    op.drop_column('project', 'is_default_lib_project')
    op.drop_column('project', 'is_lib_project')
