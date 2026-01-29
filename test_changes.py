#!/usr/bin/env python3
"""Quick syntax check for the wxmeow application."""
import sys
import os

# Add the project root to the path
sys.path.insert(0, '/home/blackcap/gits/wxmeow')

def test_imports():
    """Test that the main application modules can be imported."""
    try:
        # Test importing the main modules
        from wxmeow.views import main
        from wxmeow import app
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        return False

def test_template_syntax():
    """Test that the template can be rendered without syntax errors."""
    try:
        from wxmeow import app
        with app.app_context():
            from flask import render_template
            # Test simple template rendering
            result = render_template('base.html', title='test', wxmeow=None, pic=None)
            if result:
                print("✓ Template syntax OK")
                return True
    except Exception as e:
        print(f"✗ Template syntax error: {e}")
        return False

if __name__ == "__main__":
    print("Testing wxmeow application...")
    
    success = True
    success &= test_imports()
    success &= test_template_syntax()
    
    if success:
        print("\n✓ All tests passed - changes look good!")
        sys.exit(0)
    else:
        print("\n✗ Some tests failed")
        sys.exit(1)