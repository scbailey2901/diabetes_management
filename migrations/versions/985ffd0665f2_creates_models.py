"""Creates Models

Revision ID: 985ffd0665f2
Revises: 
Create Date: 2024-06-18 09:09:30.411128

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '985ffd0665f2'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('caregivers',
    sa.Column('cid', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(length=256), nullable=True),
    sa.Column('username', sa.String(length=200), nullable=True),
    sa.Column('type', sa.Enum('NURSE', 'DOCTOR', 'FAMILY', name='caregivertype'), nullable=True),
    sa.Column('age', sa.Integer(), nullable=True),
    sa.Column('dob', sa.DateTime(), nullable=True),
    sa.Column('email', sa.String(length=256), nullable=True),
    sa.Column('password', sa.String(length=200), nullable=True),
    sa.Column('phonenumber', sa.String(length=15), nullable=True),
    sa.Column('gender', sa.Enum('MALE', 'FEMALE', name='gender'), nullable=True),
    sa.Column('consentForData', sa.String(length=20), nullable=True),
    sa.Column('joined_on', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('cid'),
    sa.UniqueConstraint('username')
    )
    op.create_table('patients',
    sa.Column('pid', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('age', sa.Integer(), nullable=True),
    sa.Column('dob', sa.DateTime(), nullable=True),
    sa.Column('email', sa.String(length=256), nullable=True),
    sa.Column('username', sa.String(length=200), nullable=True),
    sa.Column('password', sa.String(length=256), nullable=False),
    sa.Column('phonenumber', sa.String(length=15), nullable=True),
    sa.Column('gender', sa.Enum('MALE', 'FEMALE', name='gender'), nullable=False),
    sa.Column('consentForData', sa.String(length=20), nullable=True),
    sa.Column('joined_on', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('pid'),
    sa.UniqueConstraint('username')
    )
    op.create_table('credentials',
    sa.Column('crid', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('filename', sa.String(length=200), nullable=True),
    sa.Column('credentialtype', sa.Enum('MBBS_DEGREE', 'NURSING_DEGREE', 'MEDICAL_LICENSE', name='credentialtype'), nullable=True),
    sa.Column('caregiver_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['caregiver_id'], ['caregivers.cid'], ),
    sa.PrimaryKeyConstraint('crid')
    )
    op.create_table('healthrecord',
    sa.Column('hrid', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('weight', sa.Integer(), nullable=True),
    sa.Column('weightUnits', sa.String(length=50), nullable=True),
    sa.Column('height', sa.Float(), nullable=True),
    sa.Column('heightUnits', sa.String(length=50), nullable=True),
    sa.Column('isSmoker', sa.Boolean(), nullable=True),
    sa.Column('isDrinker', sa.Boolean(), nullable=True),
    sa.Column('hasHighBP', sa.Boolean(), nullable=True),
    sa.Column('hasHighChol', sa.Boolean(), nullable=True),
    sa.Column('hasHeartDisease', sa.Boolean(), nullable=True),
    sa.Column('hadHeartAttack', sa.Boolean(), nullable=True),
    sa.Column('hadStroke', sa.Boolean(), nullable=True),
    sa.Column('hasTroubleWalking', sa.Boolean(), nullable=True),
    sa.Column('patient_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['patient_id'], ['patients.pid'], ),
    sa.PrimaryKeyConstraint('hrid')
    )
    op.create_table('medication',
    sa.Column('mid', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(length=256), nullable=True),
    sa.Column('unit', sa.String(length=256), nullable=True),
    sa.Column('recommendedFrequency', sa.Integer(), nullable=True),
    sa.Column('dosage', sa.Integer(), nullable=True),
    sa.Column('inventory', sa.Integer(), nullable=True),
    sa.Column('pid', sa.Integer(), nullable=True),
    sa.Column('creator', sa.String(length=256), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('lastupdated_by', sa.String(length=256), nullable=True),
    sa.ForeignKeyConstraint(['pid'], ['patients.pid'], ),
    sa.PrimaryKeyConstraint('mid')
    )
    op.create_table('patient_caregiver',
    sa.Column('patient_id', sa.Integer(), nullable=True),
    sa.Column('caregiver_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['caregiver_id'], ['caregivers.cid'], ),
    sa.ForeignKeyConstraint(['patient_id'], ['patients.pid'], )
    )
    op.create_table('alert',
    sa.Column('aid', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('msg', sa.String(length=256), nullable=True),
    sa.Column('type', sa.Enum('MEDICATION', 'BP_TOO_LOW', 'AT_RISK_OF_EMERGENCY', 'EAT_MEAL', 'TOO_MUCH_SALT', 'TOO_MUCH_SUGAR', name='alerttype'), nullable=True),
    sa.Column('date_time', sa.DateTime(), nullable=True),
    sa.Column('pid', sa.Integer(), nullable=True),
    sa.Column('mid', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['mid'], ['medication.mid'], ),
    sa.ForeignKeyConstraint(['pid'], ['patients.pid'], ),
    sa.PrimaryKeyConstraint('aid')
    )
    op.create_table('bloodpressurelevels',
    sa.Column('bplID', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('bloodPressureLevel', sa.Integer(), nullable=True),
    sa.Column('unit', sa.String(length=150), nullable=True),
    sa.Column('dateAndTimeRecorded', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('patient_id', sa.Integer(), nullable=True),
    sa.Column('creator', sa.String(length=256), nullable=True),
    sa.Column('hrid', sa.Integer(), nullable=True),
    sa.Column('notes', sa.String(length=256), nullable=True),
    sa.ForeignKeyConstraint(['hrid'], ['healthrecord.hrid'], ),
    sa.ForeignKeyConstraint(['patient_id'], ['patients.pid'], ),
    sa.PrimaryKeyConstraint('bplID')
    )
    op.create_table('bloodsugarlevels',
    sa.Column('bslID', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('bloodSugarLevel', sa.Integer(), nullable=True),
    sa.Column('unit', sa.String(length=150), nullable=True),
    sa.Column('dateAndTimeRecorded', sa.DateTime(), nullable=True),
    sa.Column('creator', sa.String(length=256), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('patient_id', sa.Integer(), nullable=True),
    sa.Column('hrid', sa.Integer(), nullable=True),
    sa.Column('notes', sa.String(length=256), nullable=True),
    sa.ForeignKeyConstraint(['hrid'], ['healthrecord.hrid'], ),
    sa.ForeignKeyConstraint(['patient_id'], ['patients.pid'], ),
    sa.PrimaryKeyConstraint('bslID')
    )
    op.create_table('medicationaudit',
    sa.Column('auid', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('mid', sa.Integer(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('updated_by', sa.String(length=256), nullable=True),
    sa.ForeignKeyConstraint(['mid'], ['medication.mid'], ),
    sa.PrimaryKeyConstraint('auid')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('medicationaudit')
    op.drop_table('bloodsugarlevels')
    op.drop_table('bloodpressurelevels')
    op.drop_table('alert')
    op.drop_table('patient_caregiver')
    op.drop_table('medication')
    op.drop_table('healthrecord')
    op.drop_table('credentials')
    op.drop_table('patients')
    op.drop_table('caregivers')
    # ### end Alembic commands ###
