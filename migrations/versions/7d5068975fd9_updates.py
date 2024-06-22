"""Updates

Revision ID: 7d5068975fd9
Revises: bb7d53129098
Create Date: 2024-06-22 00:20:16.424873

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '7d5068975fd9'
down_revision = 'bb7d53129098'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('alert', schema=None) as batch_op:
        batch_op.drop_constraint('alert_ibfk_1', type_='foreignkey')
        batch_op.drop_column('mid')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('alert', schema=None) as batch_op:
        batch_op.add_column(sa.Column('mid', mysql.INTEGER(), autoincrement=False, nullable=True))
        batch_op.create_foreign_key('alert_ibfk_1', 'medication', ['mid'], ['mid'])

    # ### end Alembic commands ###
