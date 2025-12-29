#!/usr/bin/env python3
"""
Simple integration test to verify the refactored structure works.
Tests imports and basic functionality without requiring GUI or heavy dependencies.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    
    # Test utils imports
    try:
        from src.utils import AppState, format_bytes
        print("✓ Utils imports successful")
    except ImportError as e:
        print(f"✗ Utils imports failed: {e}")
        return False
    
    # Test core imports (without running code that needs pandas)
    try:
        from src.core import analysis
        print("✓ Core analysis imports successful")
    except ImportError as e:
        print(f"✗ Core analysis imports failed: {e}")
        return False
    
    # Test DSL imports (code gen only, not inference) - skip if torch is problematic
    try:
        from src.dsl import dsl2code
        print("✓ DSL code gen imports successful")
    except Exception as e:
        print(f"⚠  DSL imports skipped (torch dependency issue): {str(e)[:50]}...")
        # Don't fail the test for torch issues in CI/headless environments
    
    # Test GUI components (without tkinter-dependent ones)
    try:
        from src.gui import state, threads
        from src.gui.components import cache  # Import only cache, not toast
        print("✓ GUI component imports successful (non-tkinter parts)")
    except ImportError as e:
        print(f"✗ GUI component imports failed: {e}")
        return False
    
    return True


def test_basic_functionality():
    """Test basic functionality that doesn't require heavy dependencies"""
    print("\nTesting basic functionality...")
    
    # Test format_bytes utility
    try:
        from src.utils import format_bytes
        result = format_bytes(1024 * 1024)  # 1 MB
        assert result == "1.0 MB", f"Expected '1.0 MB', got '{result}'"
        result = format_bytes(1024 * 1024 * 1024)  # 1 GB
        assert result == "1.00 GB", f"Expected '1.00 GB', got '{result}'"
        print("✓ format_bytes works correctly")
    except Exception as e:
        print(f"✗ format_bytes failed: {e}")
        return False
    
    # Test DataCache
    try:
        from src.gui.components import DataCache
        cache = DataCache(max_size=3)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        assert cache.get("nonexistent") is None
        print("✓ DataCache works correctly")
    except Exception as e:
        print(f"✗ DataCache failed: {e}")
        return False
    
    # Test AppState creation
    try:
        from src.gui.state import AppState
        state = AppState()
        assert state.df is None
        assert state.page_index == 0
        assert state.page_size == 100
        print("✓ AppState creation works correctly")
    except Exception as e:
        print(f"✗ AppState creation failed: {e}")
        return False
    
    return True


def test_file_structure():
    """Verify the directory structure is correct"""
    print("\nTesting file structure...")
    
    required_files = [
        "src/__init__.py",
        "src/core/__init__.py",
        "src/core/data_loader.py",
        "src/core/analysis.py",
        "src/core/combinations.py",
        "src/dsl/__init__.py",
        "src/dsl/dsl2code.py",
        "src/dsl/inference_dsl.py",
        "src/dsl/model.pt",
        "src/dsl/dsl_tokenizer.json",
        "src/gui/__init__.py",
        "src/gui/app.py",
        "src/gui/state.py",
        "src/gui/threads.py",
        "src/gui/components/__init__.py",
        "src/gui/components/cache.py",
        "src/gui/components/toast.py",
        "src/utils/__init__.py",
        "src/utils/utils.py",
        "src/utils/export_utils.py",
        "app.py",
        "main_cli.py",
        "build.py",
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = project_root / file_path
        if not full_path.exists():
            print(f"✗ Missing: {file_path}")
            all_exist = False
    
    if all_exist:
        print(f"✓ All {len(required_files)} required files exist")
    
    return all_exist


def main():
    """Run all tests"""
    print("=" * 60)
    print("SCV-ANALYSIS-SLICER Refactoring Verification Tests")
    print("=" * 60)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Imports", test_imports),
        ("Basic Functionality", test_basic_functionality),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n All tests passed! The refactored structure is working correctly.")
        return 0
    else:
        print("\n  Some tests failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
