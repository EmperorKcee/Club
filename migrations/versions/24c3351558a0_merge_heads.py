"""merge heads

Revision ID: 24c3351558a0
Revises: add_is_home_to_match, add_player_stats_table
Create Date: 2025-11-06 13:44:27.668562

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '24c3351558a0'
down_revision = ('add_is_home_to_match', 'add_player_stats_table')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
