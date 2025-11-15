#!/usr/bin/env python3
"""
Script to test account statistics by creating sample player accounts
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Player, PlayerUser

def test_account_stats():
    """Test account statistics by creating sample accounts"""
    with app.app_context():
        print("🧪 Testing account statistics...")
        
        try:
            # Get all players
            players = Player.query.all()
            print(f"📊 Total players: {len(players)}")
            
            # Count existing accounts
            existing_accounts = PlayerUser.query.count()
            print(f"🔐 Existing accounts: {existing_accounts}")
            
            # Create accounts for first 2 players if they don't have accounts
            accounts_created = 0
            for i, player in enumerate(players[:2]):
                if not player.user_account:
                    # Create account for this player
                    player_account = PlayerUser(
                        player_id=player.id,
                        username=f"{player.first_name.lower()}.{player.last_name.lower()}",
                        email=player.email or f"{player.first_name.lower()}.{player.last_name.lower()}@zambiafc.com"
                    )
                    player_account.set_password('player123')
                    db.session.add(player_account)
                    accounts_created += 1
                    print(f"✅ Created account for {player.full_name}")
            
            if accounts_created > 0:
                db.session.commit()
                print(f"💾 Committed {accounts_created} new accounts")
            else:
                print("ℹ️  No new accounts needed")
            
            # Show final statistics
            total_players = Player.query.count()
            players_with_accounts = db.session.query(Player).join(PlayerUser, Player.id == PlayerUser.player_id).count()
            players_without_accounts = total_players - players_with_accounts
            
            print("\n📈 Final Statistics:")
            print(f"   Total Players: {total_players}")
            print(f"   With Accounts: {players_with_accounts}")
            print(f"   Without Accounts: {players_without_accounts}")
            print(f"   Account Coverage: {(players_with_accounts/total_players*100):.1f}%" if total_players > 0 else "   Account Coverage: 0%")
            
            print("\n🎯 Test completed successfully!")
            print("   Visit: http://localhost:5000/players")
            print("   Login: admin / admin123")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            db.session.rollback()

if __name__ == '__main__':
    test_account_stats()