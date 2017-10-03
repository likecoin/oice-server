"""Add position to tag and remove mptt columns

Revision ID: 518080db1b4
Revises: 5318517efb5
Create Date: 2015-06-15 18:59:55.020541

"""

# revision identifiers, used by Alembic.
revision = '518080db1b4'
down_revision = '5318517efb5'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('tag',
        sa.Column('position', sa.Integer, nullable=False, default="")
    )
    op.create_index('tag_position_idx', 'tag', ['position'])

    op.drop_constraint('tag_ibfk_3', table_name='tag', type_="foreignkey") # parent_id foreign constraint
    op.drop_index('tag_level_idx', table_name='tag')
    op.drop_index('tag_rgt_ids', table_name='tag')
    op.drop_index('tag_lft_idx', table_name='tag')
    op.drop_index('tree_id_idx', table_name='tag')
    op.drop_column('tag', 'parent_id')
    op.drop_column('tag', 'level')
    op.drop_column('tag', 'rgt')
    op.drop_column('tag', 'lft')
    op.drop_column('tag', 'tree_id')


def downgrade():
    op.drop_index('tag_position_idx', table_name='tag')
    op.drop_column('tag', 'position')

    op.add_column('tag', sa.Column('tree_id', sa.Integer))
    op.add_column('tag', sa.Column('lft', sa.Integer, nullable=False))
    op.add_column('tag', sa.Column('rgt', sa.Integer, nullable=False))
    op.add_column('tag', sa.Column('level', sa.Integer, nullable=False, default=0))
    op.add_column('tag', sa.Column('parent_id', sa.Integer,
        sa.ForeignKey('tag.id', ondelete='CASCADE')))

    op.create_index('tree_id_idx', 'tag', ['tree_id'])
    op.create_index('tag_lft_idx', 'tag', ['lft'])
    op.create_index('tag_rgt_ids', 'tag', ['rgt'])
    op.create_index('tag_level_idx', 'tag', ['level'])
