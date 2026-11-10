"""add_sponsorship_and_source_to_jobs_applied

Revision ID: 3e926fc26946
Revises: f3a8c2d1e905
Create Date: 2026-11-09 04:01:31.583849

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3e926fc26946'
down_revision: Union[str, Sequence[str], None] = 'f3a8c2d1e905'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


sponsorship_status_enum = sa.Enum(
    'confirmed', 'explicitly_unavailable', 'possible', 'no_info', 'requires_clarification',
    name='sponsorshipstatus',
)


def upgrade() -> None:
    sponsorship_status_enum.create(op.get_bind(), checkfirst=True)
    op.add_column('jobs_applied', sa.Column('source', sa.String(), nullable=True))
    op.add_column('jobs_applied', sa.Column('posted_date', sa.Date(), nullable=True))
    op.add_column('jobs_applied', sa.Column('deadline', sa.Date(), nullable=True))
    op.add_column('jobs_applied', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('jobs_applied', sa.Column('sponsorship_status', sponsorship_status_enum, nullable=True))
    op.add_column('jobs_applied', sa.Column('sponsorship_evidence', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('jobs_applied', 'sponsorship_evidence')
    op.drop_column('jobs_applied', 'sponsorship_status')
    op.drop_column('jobs_applied', 'description')
    op.drop_column('jobs_applied', 'deadline')
    op.drop_column('jobs_applied', 'posted_date')
    op.drop_column('jobs_applied', 'source')
    sponsorship_status_enum.drop(op.get_bind(), checkfirst=True)
