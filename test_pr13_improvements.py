#!/usr/bin/env python3
"""
Test script to validate that our changes work correctly.
"""

import os
import sys
from pathlib import Path

def test_constants():
    """Test that all constants are properly defined."""
    print("🧪 Testing constants...")
    
    # Test single_instance constants
    import single_instance
    assert hasattr(single_instance, 'PROCESS_QUERY_INFORMATION')
    assert hasattr(single_instance, 'ERROR_ALREADY_EXISTS')
    assert hasattr(single_instance, 'WINDOW_OPERATION_TIMEOUT_MS')
    print("  ✓ single_instance constants defined")
    
    # Test app constants  
    import ast
    with open('app.py', 'r', encoding='utf-8') as f:
        app_content = f.read()
    
    assert 'TOAST_AUTO_CLOSE_TIMEOUT_MS' in app_content
    assert 'FADE_ANIMATION_STEP_MS' in app_content
    assert 'THEME_TRANSITION_DELAY_MS' in app_content
    print("  ✓ app.py timeout constants defined")
    
    # Test build constants
    import build_constants
    assert hasattr(build_constants, 'EXECUTABLE_NAME')
    assert hasattr(build_constants, 'BYTES_PER_MB')
    assert hasattr(build_constants, 'EXCLUDED_MODULES')
    print("  ✓ build_constants defined")

def test_batch_file_syntax():
    """Test batch file has proper delayed expansion enabled."""
    print("🧪 Testing batch file syntax...")
    
    with open('build_new.bat', 'r', encoding='utf-8') as f:
        batch_content = f.read()
    
    assert 'setlocal EnableDelayedExpansion' in batch_content
    assert '!size_mb!' in batch_content
    print("  ✓ batch file uses delayed expansion")

def test_error_handling():
    """Test improved error handling in single_instance."""
    print("🧪 Testing error handling...")
    
    from single_instance import SingleInstanceManager
    manager = SingleInstanceManager('Test')
    
    # Test that the new method exists
    assert hasattr(manager, '_remove_topmost_safely')
    
    # Test that it can be called safely (should not raise)
    manager._remove_topmost_safely()
    print("  ✓ Error handling methods work")

def test_file_syntax():
    """Test that all Python files have valid syntax."""
    print("🧪 Testing file syntax...")
    
    python_files = [
        'single_instance.py',
        'build_constants.py', 
        'build.py'
    ]
    
    for file_path in python_files:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    compile(f.read(), file_path, 'exec')
                    print(f"  ✓ {file_path} syntax valid")
                except SyntaxError as e:
                    print(f"  ❌ {file_path} syntax error: {e}")
                    return False
    
    return True

def main():
    """Run all tests."""
    print("🚀 Running validation tests for PR #13 improvements...\n")
    
    try:
        test_constants()
        test_batch_file_syntax()
        test_error_handling()
        
        if test_file_syntax():
            print("\n✅ All tests passed! PR #13 improvements implemented successfully.")
            return True
        else:
            print("\n❌ Some tests failed!")
            return False
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)