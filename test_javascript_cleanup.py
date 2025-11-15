#!/usr/bin/env python3
"""
Test script to verify JavaScript cleanup was successful
"""

import sys
import os
import re
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_javascript_cleanup():
    """Test that JavaScript duplications have been removed"""
    print("🧪 Testing JavaScript Cleanup")
    print("=" * 50)
    
    # Read the players.html file
    try:
        with open('templates/players.html', 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("✅ Successfully read players.html template")
        
        # Test 1: Check for duplicate DOMContentLoaded listeners
        dom_loaded_matches = re.findall(r'document\.addEventListener\([\'"]DOMContentLoaded[\'"]', content)
        print(f"📊 DOMContentLoaded listeners found: {len(dom_loaded_matches)}")
        
        if len(dom_loaded_matches) == 1:
            print("✅ PASS: Single DOMContentLoaded listener (no duplicates)")
        else:
            print(f"❌ FAIL: Found {len(dom_loaded_matches)} DOMContentLoaded listeners (should be 1)")
        
        # Test 2: Check for duplicate function definitions
        function_tests = [
            ('exportPlayers', r'function exportPlayers\('),
            ('printPlayers', r'function printPlayers\('),
            ('showNotification', r'function showNotification\('),
            ('initializeDeleteHandlers', r'function initializeDeleteHandlers\('),
            ('initializeViewToggle', r'function initializeViewToggle\(')
        ]
        
        print("\n🔍 Function Definition Analysis:")
        all_functions_ok = True
        
        for func_name, pattern in function_tests:
            matches = re.findall(pattern, content)
            count = len(matches)
            
            if count == 1:
                print(f"✅ {func_name}: 1 definition (correct)")
            elif count == 0:
                print(f"⚠️  {func_name}: 0 definitions (missing?)")
                all_functions_ok = False
            else:
                print(f"❌ {func_name}: {count} definitions (duplicated!)")
                all_functions_ok = False
        
        # Test 3: Check for organized initialization
        init_functions = [
            'initializeViewToggle()',
            'initializeDeleteHandlers()',
            'initializeFilters()',
            'initializeCardAnimations()',
            'initializeResetFilters()'
        ]
        
        print("\n🏗️  Initialization Structure:")
        init_found = 0
        for init_func in init_functions:
            if init_func in content:
                print(f"✅ Found: {init_func}")
                init_found += 1
            else:
                print(f"❌ Missing: {init_func}")
        
        # Test 4: Check for console logging (debugging)
        console_logs = re.findall(r'console\.log\(', content)
        print(f"\n🐛 Debug logging: {len(console_logs)} console.log statements found")
        
        if len(console_logs) > 0:
            print("✅ PASS: Debug logging is present for troubleshooting")
        else:
            print("⚠️  WARNING: No debug logging found")
        
        # Test 5: Check for proper error handling
        try_catch_blocks = re.findall(r'try\s*{', content)
        print(f"🛡️  Error handling: {len(try_catch_blocks)} try-catch blocks found")
        
        # Summary
        print("\n" + "=" * 50)
        print("📋 CLEANUP SUMMARY:")
        
        if len(dom_loaded_matches) == 1:
            print("✅ DOMContentLoaded: Consolidated to single listener")
        else:
            print("❌ DOMContentLoaded: Still has duplicates")
        
        if all_functions_ok:
            print("✅ Functions: No duplicates found")
        else:
            print("❌ Functions: Duplicates or missing functions detected")
        
        if init_found >= 4:
            print("✅ Structure: Well-organized initialization")
        else:
            print("❌ Structure: Missing initialization functions")
        
        print(f"✅ Error Handling: {len(try_catch_blocks)} try-catch blocks")
        print(f"✅ Debug Support: {len(console_logs)} console.log statements")
        
        # Overall assessment
        if (len(dom_loaded_matches) == 1 and all_functions_ok and init_found >= 4):
            print("\n🎉 OVERALL: JavaScript cleanup SUCCESSFUL!")
            print("   The code is now clean, organized, and duplicate-free.")
        else:
            print("\n⚠️  OVERALL: JavaScript cleanup needs attention")
            print("   Some issues were found that should be addressed.")
            
    except FileNotFoundError:
        print("❌ ERROR: Could not find templates/players.html")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_javascript_cleanup()