#!/usr/bin/env python3
"""
Test script for enhanced visualization features
"""
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for testing

# Import the enhanced visualization functions
from visualization import (
    plot_generic, plot_regression_with_ci, plot_distribution_comparison,
    plot_pair_correlation, plot_advanced_categorical
)

def create_test_data():
    """Create sample data for testing"""
    np.random.seed(42)
    n = 1000
    
    data = {
        'numeric1': np.random.normal(100, 15, n),
        'numeric2': np.random.normal(50, 10, n),
        'numeric3': np.random.exponential(2, n),
        'category1': np.random.choice(['A', 'B', 'C', 'D'], n, p=[0.4, 0.3, 0.2, 0.1]),
        'category2': np.random.choice(['X', 'Y', 'Z'], n),
        'date': pd.date_range('2023-01-01', periods=n, freq='D')
    }
    
    # Add some correlation
    data['numeric2'] = data['numeric2'] + 0.7 * data['numeric1'] + np.random.normal(0, 5, n)
    
    return pd.DataFrame(data)

def test_basic_plots():
    """Test basic plot functionality with new plot types"""
    print("Testing basic plot types...")
    df = create_test_data()
    
    # Test new plot types
    plot_types = ["Violin", "Density", "QQ Plot", "Ridge"]
    
    for plot_type in plot_types:
        try:
            print(f"  Testing {plot_type}...")
            # Create a mock texture and parent tag for testing
            plot_generic(df, 'numeric1', plot_type, 'test_tex', 'test_parent')
            print(f"    ✓ {plot_type} plot generated successfully")
        except Exception as e:
            print(f"    ✗ {plot_type} plot failed: {e}")

def test_advanced_plots():
    """Test advanced visualization functions"""
    print("Testing advanced plot functions...")
    df = create_test_data()
    
    try:
        print("  Testing regression plot...")
        plot_regression_with_ci(df, 'numeric1', 'numeric2', 'test_parent')
        print("    ✓ Regression plot generated successfully")
    except Exception as e:
        print(f"    ✗ Regression plot failed: {e}")
    
    try:
        print("  Testing distribution comparison...")
        plot_distribution_comparison(df, 'numeric1', 'category1', 'test_parent')
        print("    ✓ Distribution comparison plot generated successfully")
    except Exception as e:
        print(f"    ✗ Distribution comparison plot failed: {e}")
    
    try:
        print("  Testing pair correlation...")
        plot_pair_correlation(df, ['numeric1', 'numeric2', 'numeric3'], parent_tag='test_parent')
        print("    ✓ Pair correlation plot generated successfully")
    except Exception as e:
        print(f"    ✗ Pair correlation plot failed: {e}")
    
    try:
        print("  Testing advanced categorical...")
        plot_advanced_categorical(df, 'category1', 'test_parent')
        print("    ✓ Advanced categorical plot generated successfully")
    except Exception as e:
        print(f"    ✗ Advanced categorical plot failed: {e}")

def test_module_imports():
    """Test that all required modules can be imported"""
    print("Testing module imports...")
    
    try:
        import seaborn
        print("  ✓ seaborn imported successfully")
    except ImportError as e:
        print(f"  ✗ seaborn import failed: {e}")
    
    try:
        import scipy.stats
        print("  ✓ scipy.stats imported successfully")
    except ImportError as e:
        print(f"  ✗ scipy.stats import failed: {e}")
    
    try:
        import matplotlib.pyplot as plt
        print("  ✓ matplotlib imported successfully")
    except ImportError as e:
        print(f"  ✗ matplotlib import failed: {e}")

if __name__ == "__main__":
    print("=== Enhanced Visualization Test Suite ===")
    
    # Test imports first
    test_module_imports()
    print()
    
    # Test basic plots
    test_basic_plots()
    print()
    
    # Test advanced plots
    test_advanced_plots()
    print()
    
    print("=== Test Suite Complete ===")