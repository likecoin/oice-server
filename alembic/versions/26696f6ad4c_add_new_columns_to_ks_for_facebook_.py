"""Add new columns to ks for Facebook sharing

Revision ID: 26696f6ad4c
Revises: 3a7df67dadd
Create Date: 2016-08-18 11:36:26.800093

"""

# revision identifiers, used by Alembic.
revision = '26696f6ad4c'
down_revision = '3a7df67dadd'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    op.add_column('ks', sa.Column('og_description', sa.Unicode(1024), nullable=False, server_default=""))
    op.add_column('ks', sa.Column('og_image', sa.Unicode(1024), nullable=True))
    op.add_column('ks', sa.Column('og_locale', sa.Unicode(5), nullable=False, server_default="zh_HK"))

def downgrade():
    op.drop_column('ks', 'og_locale')
    op.drop_column('ks', 'og_image')
    op.drop_column('ks', 'og_description')
