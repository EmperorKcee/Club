#!/usr/bin/env python3
"""
Test the login CSRF fix
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app

def test_login_csrf():
    """Test that login works with CSRF tokens"""
    print("🔐 Testing Login CSRF Fix")
    print("=" * 50)
    
    with app.test_client() as client:
        # Test 1: Get login page
        print("1. Getting login page...")
        response = client.get('/login')
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Login page loads successfully")
        else:
            print("   ❌ Login page failed to load")
            return
        
        # Test 2: Check if CSRF token is in the response
        response_text = response.get_data(as_text=True)
        if 'csrf_token' in response_text:
            print("   ✅ CSRF token found in login page")
        else:
            print("   ❌ CSRF token not found in login page")
        
        # Test 3: Try login without CSRF token (should fail)
        print("\n2. Testing login without CSRF token...")
        login_data_no_csrf = {
            'username': 'test_user',
            'password': 'test_password'
        }
        
        response = client.post('/login', data=login_data_no_csrf)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 400:
            print("   ✅ Login rejected without CSRF token (security working)")
        else:
            print("   ⚠️  Login not rejected without CSRF token")
        
        # Test 4: Try login with CSRF token
        print("\n3. Testing login with CSRF token...")
        
        # Get a fresh page to get CSRF token
        response = client.get('/login')
        
        # Extract CSRF token from the form (this is a simplified approach)
        # In a real test, you'd parse the HTML properly
        response_text = response.get_data(as_text=True)
        
        # Try to find csrf_token value in the HTML
        import re
        csrf_match = re.search(r'name="csrf_token"[^>]*value="([^"]*)"', response_text)
        
        if csrf_match:
            csrf_token = csrf_match.group(1)
            print(f"   🔑 Found CSRF token: {csrf_token[:20]}...")
            
            login_data_with_csrf = {
                'username': 'chrisk11',  # Use real username
                'password': 'wrongpassword',  # Wrong password to test validation
                'csrf_token': csrf_token
            }
            
            response = client.post('/login', data=login_data_with_csrf)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 400 and b'CSRF token is missing' in response.get_data():
                print("   ❌ Still getting CSRF token error")
            elif response.status_code == 200:
                print("   ✅ CSRF token accepted (form validation working)")
            elif response.status_code == 302:
                print("   ✅ Login successful (redirected)")
            else:
                print(f"   ⚠️  Unexpected response: {response.status_code}")
        else:
            print("   ❌ Could not extract CSRF token from form")
        
        print("\n🎯 Test Summary:")
        print("If you're still getting CSRF errors, check:")
        print("1. Browser cache - clear it completely")
        print("2. Session cookies - delete them")
        print("3. Multiple tabs - close all and try fresh")
        print("4. Form submission method - ensure it's POST")

if __name__ == "__main__":
    test_login_csrf()