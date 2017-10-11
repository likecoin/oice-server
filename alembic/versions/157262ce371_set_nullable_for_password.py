"""Set nullable for password

Revision ID: 157262ce371
Revises: 26696f6ad4c
Create Date: 2016-09-29 12:45:17.256526

"""

# revision identifiers, used by Alembic.
revision = '157262ce371'
down_revision = '26696f6ad4c'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from sqlalchemy_utils import PasswordType

def upgrade():
    op.alter_column('user', 'password',
        existing_type=PasswordType(schemes=['pbkdf2_sha512']),
        nullable=True
        )

def downgrade():
    op.alter_column('user', 'password',
        existing_type=PasswordType(schemes=['pbkdf2_sha512']),
        nullable=False
        )
