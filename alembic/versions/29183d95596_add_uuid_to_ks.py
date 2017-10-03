"""add uuid to ks

Revision ID: 29183d95596
Revises: 23cc43a54db
Create Date: 2015-09-16 19:34:45.510995

"""
import uuid
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '29183d95596'
down_revision = '23cc43a54db'
branch_labels = None
depends_on = None


def upgrade():

    connection = op.get_bind()

    ks_table = sa.Table(
        'ks',
        sa.MetaData(),
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('uuid', sa.Unicode(32))
    )

    op.add_column(
        'ks', sa.Column('uuid', sa.Unicode(32), nullable=True)
    )

    for ks in connection.execute(ks_table.select()):
        if ks.uuid is None:
            connection.execute(
                ks_table.update().where(
                    ks_table.c.id == ks.id
                ).values(
                    uuid=uuid.uuid4().hex
                )
            )

    op.create_unique_constraint("uq_ks_uuid", "ks", ["uuid"])
    op.alter_column(
        'ks', 'uuid', existing_type=sa.Unicode(32), nullable=False,
        existing_nullable=True, server_default='')


def downgrade():

    op.drop_column('ks', 'uuid')
