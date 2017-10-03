"""init db

Revision ID: 21a4012088
Revises: 
Create Date: 2015-04-13 17:16:16.585435

"""

# revision identifiers, used by Alembic.
revision = '21a4012088'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'project',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('name', sa.Unicode(1024), nullable=False, default=""),
        sa.Column('extra_files', sa.Unicode(1024)),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        mysql_engine='InnoDB'
    )
    op.create_table(
        'ks',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('project_id', sa.Integer, 
            sa.ForeignKey('project.id'), nullable=False),
        sa.Column('filename', sa.Unicode(1024), nullable=False, default=""),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        mysql_engine='InnoDB'
    )
    op.create_table(
        'macro',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('name', sa.Unicode(1024), nullable=False, default=""),
        sa.Column('tagname', sa.Unicode(1024), nullable=False, default=""),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        mysql_engine='InnoDB'
    )
    op.create_table(
        'tag',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('ks_id', sa.Integer, 
            sa.ForeignKey('ks.id'), nullable=False),
        sa.Column('macro_id', sa.Integer, 
            sa.ForeignKey('macro.id'), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        mysql_engine='InnoDB'
    )
    op.create_table(
        'asset_type',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('name', sa.Unicode(1024), nullable=False, default=""),
        sa.Column('folder_name', sa.Unicode(1024), nullable=False, default=""),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        mysql_engine='InnoDB'
    )
    op.create_table(
        'asset',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('asset_type', sa.Unicode(1024), nullable=False, default=""),
        sa.Column('storage', sa.Unicode(1024), nullable=False, default=""),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        mysql_engine='InnoDB'
    )
    op.create_table(
        'attribute_definition',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('macro_id', sa.Integer, 
            sa.ForeignKey('macro.id'), nullable=False),
        sa.Column('name', sa.Unicode(1024), nullable=False, default=""),
        sa.Column('attribute_name', sa.Unicode(1024), nullable=False, default=""),
        sa.Column('asset_type', sa.Unicode(1024), nullable=False, default=""),
        sa.Column('asset_type_id', sa.Integer, 
            sa.ForeignKey('asset_type.id')),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        mysql_engine='InnoDB'
    )
    op.create_table(
        'attribute',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('attribute_definition_id', sa.Integer, 
            sa.ForeignKey('attribute_definition.id'), nullable=False),
        sa.Column('value', sa.Unicode(1024), default=""),
        sa.Column('asset_id', sa.Integer, 
            sa.ForeignKey('asset.id')),
        sa.Column('tag_id', sa.Integer, 
            sa.ForeignKey('tag.id'), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        mysql_engine='InnoDB'
    )


def downgrade():
    op.drop_table('attribute')
    op.drop_table('attribute_definition')
    op.drop_table('asset')
    op.drop_table('asset_type')
    op.drop_table('tag')
    op.drop_table('macro')
    op.drop_table('ks')
    op.drop_table('project')
