"""updates

Revision ID: 3f88a509d522
Revises: c9ee9b7cb1cf
Create Date: 2024-06-27 02:47:22.060492

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '3f88a509d522'
down_revision = 'c9ee9b7cb1cf'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('medication', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_updated_by', sa.String(length=256), nullable=True))
        batch_op.drop_column('lastupdated_by')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('medication', schema=None) as batch_op:
        batch_op.add_column(sa.Column('lastupdated_by', mysql.VARCHAR(length=256), nullable=True))
        batch_op.drop_column('last_updated_by')

    # ### end Alembic commands ###
