"""Add is_home to match

Revision ID: add_is_home_to_match
Revises: 
Create Date: 2023-11-03 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_is_home_to_match'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add is_home column with a default of True (assuming existing matches are home games)
    op.add_column('match', sa.Column('is_home', sa.Boolean(), nullable=True, server_default='1'))
    # Convert the venue column from 'home'/'away' to actual venue names
    op.execute("UPDATE match SET venue = 'Home Stadium' WHERE venue = 'home'")
    op.execute("UPDATE match SET venue = 'Away Stadium' WHERE venue = 'away'")
    # Set all existing matches as home games
    op.execute("UPDATE match SET is_home = 1")
    # Now make the column non-nullable
    op.alter_column('match', 'is_home', existing_type=sa.Boolean(), nullable=False)

def downgrade():
    # Convert back to the old format
    op.execute("UPDATE match SET venue = 'home' WHERE is_home = 1")
    op.execute("UPDATE match SET venue = 'away' WHERE is_home = 0")
    op.drop_column('match', 'is_home')
