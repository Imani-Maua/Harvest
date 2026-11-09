"""add work_arrangement and employment_type to work_experiences

Revision ID: 6fbd9a7e9686
Revises: 1ee511c7c150
Create Date: 2026-11-09 21:56:29.206313

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6fbd9a7e9686'
down_revision: Union[str, Sequence[str], None] = '1ee511c7c150'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    work_arrangement_enum = sa.Enum('hybrid', 'in_person', 'remote', name='workarrangement')
    employment_type_enum = sa.Enum('full_time', 'part_time', 'internship', 'fellowship', 'research', name='employmenttype')
    work_arrangement_enum.create(op.get_bind(), checkfirst=True)
    employment_type_enum.create(op.get_bind(), checkfirst=True)
    op.add_column('work_experiences', sa.Column('work_arrangement', work_arrangement_enum, nullable=True))
    op.add_column('work_experiences', sa.Column('employment_type', employment_type_enum, nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('work_experiences', 'employment_type')
    op.drop_column('work_experiences', 'work_arrangement')
    sa.Enum(name='employmenttype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='workarrangement').drop(op.get_bind(), checkfirst=True)
