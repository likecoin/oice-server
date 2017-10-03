"""rename tag to block

Revision ID: 52d9f7773cc
Revises: 2a9fd935315
Create Date: 2015-06-24 16:21:35.877088

"""

# revision identifiers, used by Alembic.
revision = '52d9f7773cc'
down_revision = '2a9fd935315'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():

    op.drop_constraint('attribute_ibfk_3', table_name='attribute', type_="foreignkey") # tag_id foreign constraint
    op.drop_index('tag_id', table_name='attribute')

    op.drop_index('tag_position_idx', table_name='tag')
    
    op.rename_table('tag', 'block')
    op.alter_column('attribute', 'tag_id', new_column_name='block_id', existing_type=sa.Integer)

    op.create_foreign_key('attribute_ibfk_3', 'attribute', 'block', ['block_id'], ['id'])
    op.create_index('block_id', 'block', ['id'])

    op.create_index('block_position_idx', 'block', ['position'])


def downgrade():
    op.drop_index('block_position_idx', table_name='block')

    op.drop_constraint('attribute_ibfk_3', table_name='attribute', type_="foreignkey") # tag_id foreign constraint
    op.drop_index('block_id', table_name='block')

    op.rename_table('block', 'tag')
    op.alter_column('attribute', 'block_id', new_column_name='tag_id', existing_type=sa.Integer)

    op.create_foreign_key('attribute_ibfk_3', 'attribute', 'tag', ['tag_id'], ['id'])
    op.create_index('tag_position_idx', 'tag', ['position'])
    op.create_index('tag_id', 'attribute', ['tag_id'])
