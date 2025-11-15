#!/usr/bin/env python3
"""
Script to fix database integrity issues with PlayerUser records
"""

from app import app, db
from models import Player, PlayerUser

def fix_database_integrity():
    with app.app_context():
        print("🔧 Fixing Database Integrity Issues")
        print("=" * 50)
        
        # Find PlayerUser records with invalid player_id
        orphaned_users = PlayerUser.query.filter(
            ~PlayerUser.player_id.in_(
                db.session.query(Player.id)
            )
        ).all()
        
        if orphaned_users:
            print(f"\n❌ Found {len(orphaned_users)} orphaned PlayerUser records:")
            for user in orphaned_users:
                print(f"  - PlayerUser ID: {user.id}, Username: {user.username}, Player ID: {user.player_id}")
            
            # Delete orphaned PlayerUser records
            for user in orphaned_users:
                print(f"  🗑️ Deleting orphaned PlayerUser: {user.username}")
                db.session.delete(user)
            
            db.session.commit()
            print(f"✅ Deleted {len(orphaned_users)} orphaned PlayerUser records")
        else:
            print("✅ No orphaned PlayerUser records found")
        
        # Check for PlayerUser records with NULL player_id
        null_player_users = PlayerUser.query.filter(PlayerUser.player_id.is_(None)).all()
        
        if null_player_users:
            print(f"\n❌ Found {len(null_player_users)} PlayerUser records with NULL player_id:")
            for user in null_player_users:
                print(f"  - PlayerUser ID: {user.id}, Username: {user.username}")
            
            # Delete PlayerUser records with NULL player_id
            for user in null_player_users:
                print(f"  🗑️ Deleting PlayerUser with NULL player_id: {user.username}")
                db.session.delete(user)
            
            db.session.commit()
            print(f"✅ Deleted {len(null_player_users)} PlayerUser records with NULL player_id")
        else:
            print("✅ No PlayerUser records with NULL player_id found")
        
        # Verify current state
        print("\n📊 Current Database State:")
        total_players = Player.query.count()
        total_player_users = PlayerUser.query.count()
        
        print(f"  👥 Total Players: {total_players}")
        print(f"  🔐 Total Player Users: {total_player_users}")
        
        # Check for valid relationships
        valid_relationships = db.session.query(PlayerUser).join(Player).count()
        print(f"  ✅ Valid PlayerUser-Player relationships: {valid_relationships}")
        
        if valid_relationships == total_player_users:
            print("\n🎉 All PlayerUser records have valid Player relationships!")
        else:
            print(f"\n⚠️ Warning: {total_player_users - valid_relationships} PlayerUser records may have issues")
        
        print("\n" + "=" * 50)
        print("✅ Database integrity check complete!")

if __name__ == '__main__':
    fix_database_integrity()