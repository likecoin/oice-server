"""character fgimage support

Revision ID: 3f1fa101441
Revises: da227aeb4
Create Date: 2015-08-28 11:31:57.692016

"""

# revision identifiers, used by Alembic.
revision = '3f1fa101441'
down_revision = 'da227aeb4'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():

    op.drop_table('character')

    op.create_table(
        'character',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('name', sa.Unicode(1024), nullable=False),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('project.id',
                  name='character_ibfk1')),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        mysql_engine='InnoDB'
    )

    op.create_table(
        'character_fgimages',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('character_id', sa.Integer, sa.ForeignKey('character.id',
                  name='character_fgimages_ibfk_1'), nullable=False, ),
        sa.Column('asset_id', sa.Integer, sa.ForeignKey('asset.id',
                  name='character_fgimages_ibfk_2'), nullable=False),
        mysql_engine='InnoDB'
    )


def downgrade():

    op.drop_table('character_fgimages')

    op.drop_table('character')

    op.create_table(
        'character',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('name', sa.Unicode(1024), nullable=False),
        sa.Column('macro_id', sa.Integer, sa.ForeignKey('macro.id',
                  name='character_ibfk1'), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        mysql_engine='InnoDB'
    )
