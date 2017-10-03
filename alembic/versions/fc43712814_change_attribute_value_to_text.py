"""change attribute value to text

Revision ID: fc43712814
Revises: 3f1fa101441
Create Date: 2015-09-04 17:00:08.677453

"""

# revision identifiers, used by Alembic.
revision = 'fc43712814'
down_revision = '3f1fa101441'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():

    connection = op.get_bind()

    migrationhelper = sa.Table(
        'macro',
        sa.MetaData(),
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('is_custom', sa.Boolean, server_default='0'),
        sa.Column('macro_type', sa.Unicode(1024), server_default='system')
    )

    op.alter_column('attribute', 'value', type_=sa.TEXT)
    op.add_column('macro', sa.Column('macro_type', sa.Unicode(1024), server_default='system'))

    for macro in connection.execute(migrationhelper.select()):
        if macro.is_custom:
            connection.execute(
                migrationhelper.update().where(
                    migrationhelper.c.id == macro.id
                ).values(
                    macro_type='custom'
                )
            )
        else:
            connection.execute(
                migrationhelper.update().where(
                    migrationhelper.c.id == macro.id
                ).values(
                    macro_type='system'
                )
            )

    op.drop_column('macro', 'is_custom')


def downgrade():

    connection = op.get_bind()

    op.add_column('macro', sa.Column('is_custom', sa.Boolean, server_default='0'))

    migrationhelper = sa.Table(
        'macro',
        sa.MetaData(),
        sa.Column('id', sa.Integer, primary_key=True, nullable=False),
        sa.Column('is_custom', sa.Boolean, server_default='0'),
        sa.Column('macro_type', sa.Unicode(1024), server_default='system')
    )

    for macro in connection.execute(migrationhelper.select()):
        if macro.macro_type == 'system':
            connection.execute(
                migrationhelper.update().where(
                    migrationhelper.c.id == macro.id
                ).values(
                    is_custom=0
                )
            )
        else:
            connection.execute(
                migrationhelper.update().where(
                    migrationhelper.c.id == macro.id
                ).values(
                    is_custom=1
                )
            )

    op.drop_column('macro', 'macro_type')
    op.alter_column('attribute', 'value', type_=sa.Unicode(1024))
