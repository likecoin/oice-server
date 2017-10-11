"""add user model and user project relation

Revision ID: 23cc43a54db
Revises: dcd9d5f2c7
Create Date: 2015-09-11 14:58:07.116263

"""

# revision identifiers, used by Alembic.
revision = '23cc43a54db'
down_revision = 'dcd9d5f2c7'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy_utils import PasswordType


def upgrade():
    op.create_table(
        'user',

        sa.Column('id', sa.Integer, primary_key=True, nullable=False),

        sa.Column('email', sa.Unicode(128), nullable=False, unique=True),
        sa.Column('password', PasswordType(schemes=['pbkdf2_sha512']), nullable=False),
        sa.Column('role', sa.Unicode(1024), nullable=False, server_default='user'),
        sa.Column('last_login_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        mysql_engine='InnoDB'
    )

    op.create_table(
        'user_project',

        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('user_id', sa.Integer,
                  sa.ForeignKey('user.id', name='user_project_ibfk1'), nullable=False),
        sa.Column('project_id', sa.Integer,
                  sa.ForeignKey('project.id', name='user_project_ibfk2'), nullable=False)
    )


def downgrade():
    op.drop_constraint('user_project_ibfk1', 'user_project', type="foreignkey")
    op.drop_constraint('user_project_ibfk2', 'user_project', type="foreignkey")
    op.drop_table('user')
    op.drop_table('user_project')
