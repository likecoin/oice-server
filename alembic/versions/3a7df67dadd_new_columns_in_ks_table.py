"""New columns in 'ks' table

Revision ID: 3a7df67dadd
Revises: 49f303b5493
Create Date: 2016-07-29 12:04:19.109645

"""

# revision identifiers, used by Alembic.
revision = '3a7df67dadd'
down_revision = '49f303b5493'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    op.add_column('ks', sa.Column('is_show_ad', sa.Boolean(), nullable=False, server_default='1'))

def downgrade():
    op.drop_column('ks', 'is_show_ad')
