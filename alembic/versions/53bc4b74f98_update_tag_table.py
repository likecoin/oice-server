"""update tag table

Revision ID: 53bc4b74f98
Revises: 21a4012088
Create Date: 2015-04-17 11:26:11.907367

"""

# revision identifiers, used by Alembic.
revision = '53bc4b74f98'
down_revision = '21a4012088'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('tag', sa.Column('tree_id', sa.Integer))
    op.add_column('tag', sa.Column('lft', sa.Integer, nullable=False))
    op.add_column('tag', sa.Column('rgt', sa.Integer, nullable=False))
    op.add_column('tag', sa.Column('level', sa.Integer, nullable=False, default=0))
    op.add_column('tag', sa.Column('parent_id', sa.Integer,
        sa.ForeignKey('tag.id', ondelete='CASCADE')))
    op.create_index('tag_lft_idx', 'tag', ['lft'])
    op.create_index('tag_rgt_ids', 'tag', ['rgt'])
    op.create_index('tag_level_idx', 'tag', ['level'])


def downgrade():

    op.drop_constraint('tag_ibfk_3',
        table_name='tag',
        type_="foreignkey")

    op.drop_index('tag_level_idx', table_name='tag')
    op.drop_index('tag_rgt_ids', table_name='tag')
    op.drop_index('tag_lft_idx', table_name='tag')
    op.drop_index('parent_id', table_name='tag')    

    op.drop_column('tag', 'parent_id')
    op.drop_column('tag', 'level')
    op.drop_column('tag', 'rgt')
    op.drop_column('tag', 'lft')
    op.drop_column('tag', 'tree_id')
