"""add oice modle

Revision ID: 19ee5d790ac
Revises: 15ee9d8d532
Create Date: 2015-09-25 14:41:39.919736

"""

# revision identifiers, used by Alembic.
revision = '19ee5d790ac'
down_revision = '15ee9d8d532'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'poll',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('question', sa.Unicode(1024), nullable=False),
        sa.Column('og_title', sa.Unicode(1024), nullable=False),
        sa.Column('og_description', sa.Unicode(1024), nullable=False),
        sa.Column('og_image_storage', sa.Unicode(1024), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        mysql_engine='InnoDB'
    )

    op.add_column(
        'ks',
        sa.Column('poll_id', sa.Integer,
                  sa.ForeignKey('poll.id', name='ks_ibfk_2'))
    )

    op.create_table(
        'option',
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('label', sa.Unicode(1024), nullable=False),
        sa.Column('poll_id', sa.Integer, sa.ForeignKey('poll.id',
                  name='option_ibfk_1')),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        mysql_engine='InnoDB'
    )


def downgrade():
    op.drop_table('option')

    op.drop_constraint('ks_ibfk_2', 'ks', 'foreignkey')
    op.drop_column('ks', 'poll_id')

    op.drop_table('poll')
