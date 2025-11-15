#!/usr/bin/env python3
"""
Debug script to identify the exact CSRF issue
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app

def debug_csrf_issue():
    """Debug the CSRF issue step by step"""
    print("🔍 Debugging CSRF Issue")
    print("=" * 50)
    
    with app.app_context():
        # Test 1: Check CSRF configuration
        print("1. Checking CSRF Configuration...")
        try:
            from extensions import csrf
            print(f"   ✅ CSRF extension loaded: {csrf}")
        except Exception as e:
            print(f"   ❌ CSRF extension error: {e}")
            return
        
        # Test 2: Test login flow with proper CSRF token
        print("\n2. Testing Login Flow...")
        with app.test_client() as client:
            # Get login page first to establish session
            print("   📄 Getting login page...")
            response = client.get('/login')
            print(f"   Status: {response.status_code}")
            
            # Extract CSRF token from the response if possible
            with client.session_transaction() as sess:
                print(f"   Session keys: {list(sess.keys())}")
            
            # Test login with CSRF token
            with app.test_request_context():
                from flask_wtf.csrf import generate_csrf
                csrf_token = generate_csrf()
                print(f"   🔑 Generated CSRF token: {csrf_token[:20]}...")
                
                login_data = {
                    'username': 'chrisk11',  # Use a real username
                    'password': 'wrongpassword',  # Wrong password to avoid actual login
                    'csrf_token': csrf_token
                }
                
                print("   🔐 Attempting login with CSRF token...")
                response = client.post('/login', data=login_data)
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 400:
                    response_text = response.get_data(as_text=True)
                    if 'CSRF token is missing' in response_text:
                        print("   ❌ CSRF token still not working")
                    elif 'CSRF token' in response_text:
                        print("   ❌ CSRF token validation failed")
                    else:
                        print("   ✅ CSRF token accepted (got different error)")
                elif response.status_code == 200:
                    print("   ✅ Login page returned (likely invalid credentials)")
                elif response.status_code == 302:
                    print("   ✅ Redirect occurred (login might have worked)")
                else:
                    print(f"   ⚠️  Unexpected status: {response.status_code}")
        
        # Test 3: Check if the issue is in template rendering
        print("\n3. Testing Template Rendering...")
        with app.test_request_context():
            try:
                from flask import render_template_string
                test_template = '''
                <form method="POST">
                    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                    <input type="text" name="test" value="test">
                </form>
                '''
                rendered = render_template_string(test_template)
                if 'csrf_token' in rendered and 'value=' in rendered:
                    print("   ✅ CSRF token renders correctly in templates")
                else:
                    print("   ❌ CSRF token not rendering in templates")
                    print(f"   Rendered: {rendered}")
            except Exception as e:
                print(f"   ❌ Template rendering error: {e}")
        
        # Test 4: Check actual login template
        print("\n4. Checking Login Template...")
        try:
            with open('templates/login.html', 'r') as f:
                content = f.read()
                if 'csrf_token()' in content:
                    print("   ✅ Login template has csrf_token() call")
                else:
                    print("   ❌ Login template missing csrf_token() call")
                    
                if 'name="csrf_token"' in content:
                    print("   ✅ Login template has csrf_token input field")
                else:
                    print("   ❌ Login template missing csrf_token input field")
        except Exception as e:
            print(f"   ❌ Error reading login template: {e}")
        
        print("\n🎯 Debugging Summary:")
        print("If CSRF tokens are working but you still get errors,")
        print("the issue might be:")
        print("1. Session not being maintained properly")
        print("2. CSRF token expiring too quickly")
        print("3. Multiple forms on the same page")
        print("4. JavaScript interfering with form submission")

if __name__ == "__main__":
    debug_csrf_issue()