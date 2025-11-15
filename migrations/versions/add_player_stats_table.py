"""Add PlayerStats model

Revision ID: add_player_stats_table
Revises: 
Create Date: 2025-10-03 01:23:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_player_stats_table'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create the player_stats table
    op.create_table('player_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('player_id', sa.Integer(), nullable=False),
        sa.Column('matches_played', sa.Integer(), server_default='0', nullable=False),
        sa.Column('goals', sa.Integer(), server_default='0', nullable=False),
        sa.Column('assists', sa.Integer(), server_default='0', nullable=False),
        sa.Column('yellow_cards', sa.Integer(), server_default='0', nullable=False),
        sa.Column('red_cards', sa.Integer(), server_default='0', nullable=False),
        sa.Column('clean_sheets', sa.Integer(), server_default='0', nullable=False),
        sa.Column('minutes_played', sa.Integer(), server_default='0', nullable=False),
        sa.ForeignKeyConstraint(['player_id'], ['player.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('player_id')
    )
    
    # Add any data migration logic here if needed


def downgrade():
    op.drop_table('player_stats')
