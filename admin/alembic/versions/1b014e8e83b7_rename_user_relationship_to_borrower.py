"""Rename user relationship to borrower

Revision ID: 1b014e8e83b7
Revises: 
Create Date: 2025-02-21 19:48:34.295895
"""
from alembic import op
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision = '1b014e8e83b7'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename the column in the database
    op.alter_column('books', 'borrower_id', new_column_name='user_id')


def downgrade() -> None:
    # Revert the column name change
    op.alter_column('books', 'user_id', new_column_name='borrower_id')
