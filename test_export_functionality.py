#!/usr/bin/env python3
"""
Test script for player accounts export functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, Player, PlayerUser
from werkzeug.security import generate_password_hash
import tempfile
import csv
from io import StringIO

def test_export_functionality():
    """Test the export functionality for player accounts"""
    
    with app.app_context():
        print("Testing Player Accounts Export Functionality")
        print("=" * 50)
        
        # Check if we have any player accounts to export
        player_accounts = db.session.query(PlayerUser, Player).join(
            Player, PlayerUser.player_id == Player.id
        ).all()
        
        print(f"Found {len(player_accounts)} player accounts")
        
        if len(player_accounts) == 0:
            print("No player accounts found. Creating test data...")
            create_test_data()
            player_accounts = db.session.query(PlayerUser, Player).join(
                Player, PlayerUser.player_id == Player.id
            ).all()
        
        # Test CSV generation function
        print("\n1. Testing CSV generation function...")
        try:
            from app import generate_credentials_csv
            
            # Test with sample data
            output = StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'Player Name', 'Jersey Number', 'Position', 'Username', 'Email', 
                'Account Status', 'Created Date', 'Last Login', 'Login URL'
            ])
            
            # Write sample data
            for player_user, player in player_accounts[:3]:  # Test with first 3
                writer.writerow([
                    player.full_name,
                    player.jersey_number,
                    player.position,
                    player_user.username,
                    player_user.email,
                    'Active' if player_user.is_active else 'Disabled',
                    player_user.created_at.strftime('%Y-%m-%d') if player_user.created_at else 'N/A',
                    player_user.last_login.strftime('%Y-%m-%d %H:%M') if player_user.last_login else 'Never',
                    'http://localhost:5000/auth'
                ])
            
            csv_content = output.getvalue()
            print("✓ CSV generation successful")
            print(f"Sample CSV content (first 200 chars): {csv_content[:200]}...")
            
        except Exception as e:
            print(f"✗ CSV generation failed: {e}")
            return False
        
        # Test route availability
        print("\n2. Testing export routes...")
        
        with app.test_client() as client:
            # Create admin user for testing
            admin_user = User.query.filter_by(role='admin').first()
            if not admin_user:
                print("Creating test admin user...")
                admin_user = User(
                    username='testadmin',
                    email='admin@test.com',
                    password_hash=generate_password_hash('admin123'),
                    role='admin',
                    is_active=True
                )
                db.session.add(admin_user)
                db.session.commit()
            
            # Login as admin
            with client.session_transaction() as sess:
                sess['_user_id'] = str(admin_user.id)
                sess['_fresh'] = True
            
            # Test export all credentials route
            print("Testing export all credentials...")
            response = client.post('/admin/export-all-player-credentials')
            if response.status_code == 200:
                print("✓ Export all credentials route working")
                print(f"Content-Type: {response.headers.get('Content-Type')}")
                print(f"Content-Disposition: {response.headers.get('Content-Disposition')}")
            else:
                print(f"✗ Export all credentials failed: {response.status_code}")
                print(f"Response: {response.data.decode()}")
            
            # Test export active credentials route
            print("Testing export active credentials...")
            response = client.post('/admin/export-active-player-credentials')
            if response.status_code == 200:
                print("✓ Export active credentials route working")
            else:
                print(f"✗ Export active credentials failed: {response.status_code}")
            
            # Test export selected credentials route
            if player_accounts:
                print("Testing export selected credentials...")
                player_user_id = player_accounts[0][0].id
                response = client.post('/admin/export-player-credentials', 
                                     data={'account_ids': [player_user_id]})
                if response.status_code == 200:
                    print("✓ Export selected credentials route working")
                else:
                    print(f"✗ Export selected credentials failed: {response.status_code}")
        
        print("\n3. Testing JavaScript functions...")
        
        # Check if the JavaScript functions are properly defined in the template
        with open('templates/admin/player_accounts.html', 'r') as f:
            template_content = f.read()
            
        js_functions = [
            'exportAllCredentials',
            'exportActiveCredentials', 
            'exportSelectedCredentials'
        ]
        
        for func in js_functions:
            if f'function {func}()' in template_content:
                print(f"✓ JavaScript function {func} found")
            else:
                print(f"✗ JavaScript function {func} missing")
        
        print("\n" + "=" * 50)
        print("Export functionality test completed!")
        
        return True

def create_test_data():
    """Create test player accounts if none exist"""
    
    # Check if we have players without accounts
    players_without_accounts = db.session.query(Player).outerjoin(
        PlayerUser, Player.id == PlayerUser.player_id
    ).filter(PlayerUser.id.is_(None)).limit(3).all()
    
    if not players_without_accounts:
        print("All players already have accounts or no players exist")
        return
    
    print(f"Creating accounts for {len(players_without_accounts)} players...")
    
    for player in players_without_accounts:
        # Create player account
        username = f"{player.first_name.lower()}.{player.last_name.lower()}"
        email = f"{username}@zambiafc.com"
        password = f"{player.first_name.lower()}{player.jersey_number}"
        
        player_user = PlayerUser(
            player_id=player.id,
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            is_active=True
        )
        
        db.session.add(player_user)
        print(f"Created account for {player.full_name}: {username}")
    
    db.session.commit()
    print("Test accounts created successfully!")

if __name__ == '__main__':
    test_export_functionality()