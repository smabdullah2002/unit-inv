"""Initial branches and units tables

Revision ID: 0001_initial
Revises: 
Create Date: 2026-11-10 18:20:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create branches table
    op.create_table(
        'branches',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 2. Create units table
    op.create_table(
        'units',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('branch_id', sa.Uuid(as_uuid=True), sa.ForeignKey('branches.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )

    # 3. Create indexes
    op.create_index('ix_units_branch_id', 'units', ['branch_id'])
    op.create_index('ix_units_branch_id_type', 'units', ['branch_id', 'type'])

    # 4. Create partial unique indexes
    op.create_index(
        'ix_units_branch_id_code_active',
        'units',
        ['branch_id', 'code'],
        unique=True,
        postgresql_where=sa.text('deleted_at IS NULL'),
        sqlite_where=sa.text('deleted_at IS NULL'),
    )
    op.create_index(
        'ix_units_branch_id_name_active',
        'units',
        ['branch_id', 'name'],
        unique=True,
        postgresql_where=sa.text('deleted_at IS NULL'),
        sqlite_where=sa.text('deleted_at IS NULL'),
    )


def downgrade() -> None:
    op.drop_index('ix_units_branch_id_name_active', table_name='units')
    op.drop_index('ix_units_branch_id_code_active', table_name='units')
    op.drop_index('ix_units_branch_id_type', table_name='units')
    op.drop_index('ix_units_branch_id', table_name='units')
    op.drop_table('units')
    op.drop_table('branches')

