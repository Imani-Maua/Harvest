"""add jobs_applied and network tables

Revision ID: f3a8c2d1e905
Revises: 0bc6954e0e80
Create Date: 2026-11-09 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'f3a8c2d1e905'
down_revision: Union[str, Sequence[str], None] = '0bc6954e0e80'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'jobs_applied',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company', sa.String(), nullable=False),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('job_title', sa.String(), nullable=False),
        sa.Column(
            'job_status',
            sa.Enum('watch_list', 'applied', 'in_pipeline', 'rejected', 'offered', name='jobstatus'),
            nullable=False,
        ),
        sa.Column('job_url', sa.String(), nullable=True),
        sa.Column('applied_date', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_jobs_applied_id'), 'jobs_applied', ['id'], unique=False)

    op.create_table(
        'network',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_applied_id', sa.Integer(), nullable=False),
        sa.Column('hiring_manager', sa.String(), nullable=True),
        sa.Column('technical_recruiter', sa.String(), nullable=True),
        sa.Column('peers', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('hiring_name', sa.String(), nullable=True),
        sa.Column('technical_name', sa.String(), nullable=True),
        sa.Column('peer_name', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['job_applied_id'], ['jobs_applied.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_applied_id'),
    )
    op.create_index(op.f('ix_network_id'), 'network', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_network_id'), table_name='network')
    op.drop_table('network')
    op.drop_index(op.f('ix_jobs_applied_id'), table_name='jobs_applied')
    op.drop_table('jobs_applied')
    op.execute('DROP TYPE IF EXISTS jobstatus')
