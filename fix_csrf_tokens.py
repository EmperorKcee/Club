#!/usr/bin/env python3
"""
Script to add CSRF tokens to forms that are missing them
"""

import os
import re
import glob

def fix_csrf_tokens():
    """Add CSRF tokens to forms missing them"""
    print("🔒 Adding CSRF tokens to forms...")
    
    # Templates that need CSRF token fixes
    templates_to_fix = [
        'templates/contact.html',
        'templates/_transaction_form.html',
        'templates/_transactions_section.html',
        'templates/staff/view.html',
        'templates/staff/list.html',
        'templates/settings.html',
        'templates/register.html',
        'templates/profile.html',
        'templates/players_fixed.html',
        'templates/admin/player_accounts.html',
        'templates/player/login.html',
        'templates/edit_match.html'
    ]
    
    # Pattern to find forms without CSRF tokens
    form_pattern = r'<form[^>]*method=["\']POST["\'][^>]*>'
    csrf_pattern = r'csrf_token'
    
    for template_path in templates_to_fix:
        if os.path.exists(template_path):
            print(f"📝 Processing {template_path}...")
            
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find all POST forms
            forms = re.finditer(form_pattern, content, re.IGNORECASE)
            
            modified = False
            for form_match in forms:
                form_start = form_match.end()
                
                # Check if this form already has a CSRF token
                # Look for CSRF token in the next 500 characters after form tag
                form_section = content[form_start:form_start + 500]
                
                if not re.search(csrf_pattern, form_section, re.IGNORECASE):
                    # Add CSRF token after the form tag
                    csrf_token_line = '\n                    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>'
                    
                    # Insert CSRF token after the form opening tag
                    content = content[:form_start] + csrf_token_line + content[form_start:]
                    modified = True
                    print(f"  ✅ Added CSRF token to form in {template_path}")
            
            if modified:
                with open(template_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  💾 Saved {template_path}")
            else:
                print(f"  ℹ️  No changes needed for {template_path}")
        else:
            print(f"  ⚠️  File not found: {template_path}")
    
    print("\n🎉 CSRF token fix completed!")

if __name__ == "__main__":
    fix_csrf_tokens()