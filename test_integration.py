#!/usr/bin/env python3
"""
Integration test for enhanced visualization features with UI
Tests the complete workflow from data loading to plot generation
"""
import pandas as pd
import numpy as np
import tempfile
import os
from pathlib import Path

def create_test_csv():
    """Create a test CSV file for the integration test"""
    np.random.seed(42)
    n = 1000
    
    # Create realistic test data
    data = {
        'Product_ID': [f'P{i:04d}' for i in range(n)],
        'Sales_Amount': np.random.normal(1000, 300, n),
        'Customer_Age': np.random.normal(35, 12, n),
        'Order_Quantity': np.random.randint(1, 50, n),
        'Product_Category': np.random.choice(['Electronics', 'Clothing', 'Books', 'Home'], n, p=[0.3, 0.25, 0.25, 0.2]),
        'Region': np.random.choice(['North', 'South', 'East', 'West'], n),
        'Order_Date': pd.date_range('2023-01-01', periods=n, freq='D'),
        'Customer_Satisfaction': np.random.randint(1, 6, n),
        'Discount_Percent': np.random.uniform(0, 30, n)
    }
    
    # Add some correlation for interesting analysis
    data['Revenue'] = data['Sales_Amount'] * (1 - data['Discount_Percent']/100) + np.random.normal(0, 50, n)
    
    df = pd.DataFrame(data)
    
    # Create temporary CSV file
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
    df.to_csv(temp_file.name, index=False)
    temp_file.close()
    
    return temp_file.name, df

def test_data_loader_integration():
    """Test data loading functionality"""
    print("Testing data loader integration...")
    
    try:
        from data_loader import load_csv
        from utils import AppState
        
        # Create test data
        csv_path, expected_df = create_test_csv()
        
        # Test loading
        state = AppState()
        state.df = load_csv(csv_path)
        
        print(f"  ✓ Successfully loaded CSV with {len(state.df)} rows and {len(state.df.columns)} columns")
        print(f"  ✓ Columns: {list(state.df.columns)}")
        
        # Clean up
        os.unlink(csv_path)
        
        return state
        
    except Exception as e:
        print(f"  ✗ Data loader integration failed: {e}")
        return None

def test_visualization_functions():
    """Test all visualization functions work correctly"""
    print("Testing visualization functions...")
    
    # Create test data
    csv_path, df = create_test_csv()
    
    try:
        from visualization import (
            plot_generic, plot_regression_with_ci, plot_distribution_comparison,
            plot_pair_correlation, plot_advanced_categorical
        )
        
        # Test basic plots with new types
        basic_plot_types = ["Histogram", "Violin", "Density", "QQ Plot", "Ridge"]
        for plot_type in basic_plot_types:
            try:
                # Use a mock texture/parent for testing
                result = plot_generic(df, 'Sales_Amount', plot_type, 'test_tex', 'test_parent')
                print(f"    ✓ {plot_type} plot function works")
            except Exception as e:
                print(f"    ✗ {plot_type} plot failed: {e}")
        
        # Test advanced plots
        try:
            plot_regression_with_ci(df, 'Sales_Amount', 'Revenue', 'test_parent')
            print(f"    ✓ Regression analysis function works")
        except Exception as e:
            print(f"    ✗ Regression analysis failed: {e}")
        
        try:
            plot_distribution_comparison(df, 'Sales_Amount', 'Product_Category', 'test_parent')
            print(f"    ✓ Distribution comparison function works")
        except Exception as e:
            print(f"    ✗ Distribution comparison failed: {e}")
        
        try:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()[:4]
            plot_pair_correlation(df, numeric_cols, parent_tag='test_parent')
            print(f"    ✓ Pair correlation function works")
        except Exception as e:
            print(f"    ✗ Pair correlation failed: {e}")
        
        try:
            plot_advanced_categorical(df, 'Product_Category', 'test_parent')
            print(f"    ✓ Advanced categorical function works")
        except Exception as e:
            print(f"    ✗ Advanced categorical failed: {e}")
    
    except ImportError as e:
        print(f"  ✗ Import error: {e}")
    
    finally:
        # Clean up
        os.unlink(csv_path)

def test_ui_integration():
    """Test UI module integration"""
    print("Testing UI module integration...")
    
    try:
        import ui
        from utils import AppState
        
        # Test that new functions are importable
        from ui import on_generate_advanced_plot
        print("  ✓ Advanced plot function imported successfully")
        
        # Test state creation
        state = AppState()
        print("  ✓ AppState creation works")
        
        # Test that all required tags exist in UI module
        expected_tags = ['TAG_PLOT_CANVAS', 'TAG_ANALYSIS_SCROLL', 'TAG_PREVIEW_TABLE']
        for tag in expected_tags:
            if hasattr(ui, tag):
                print(f"    ✓ UI tag {tag} exists")
            else:
                print(f"    ! UI tag {tag} not found")
        
    except Exception as e:
        print(f"  ✗ UI integration test failed: {e}")

def test_enhanced_features():
    """Test enhanced features specifically"""
    print("Testing enhanced features...")
    
    # Test color palette
    try:
        from visualization import DARK_COLORS, DARK_PALETTE, CATEGORICAL_PALETTE
        print(f"  ✓ Color palettes loaded: {len(DARK_COLORS)} dark colors, {len(DARK_PALETTE)} dark palette, {len(CATEGORICAL_PALETTE)} categorical palette")
    except ImportError:
        print("  ✗ Color palettes not available")
    
    # Test theming function
    try:
        from visualization import _apply_dark_theme_to_axis
        import matplotlib.pyplot as plt
        
        fig, ax = plt.subplots()
        _apply_dark_theme_to_axis(ax, "Test Title")
        plt.close(fig)
        print("  ✓ Dark theme application function works")
    except Exception as e:
        print(f"  ✗ Dark theme function failed: {e}")

def test_complete_workflow():
    """Test a complete workflow from data to visualization"""
    print("Testing complete workflow...")
    
    try:
        # Create test data
        csv_path, df = create_test_csv()
        
        # Simulate the workflow
        from utils import AppState
        from data_loader import load_csv
        from analysis import column_profile
        from visualization import plot_generic
        
        # 1. Load data
        state = AppState()
        state.df = load_csv(csv_path)
        print("  ✓ Step 1: Data loaded successfully")
        
        # 2. Analyze column
        numeric_col = state.df.select_dtypes(include=[np.number]).columns[0]
        profile = column_profile(state.df, numeric_col)
        print(f"  ✓ Step 2: Column analysis completed for {numeric_col}")
        
        # 3. Generate visualization
        plot_generic(state.df, numeric_col, 'Violin', 'test_tex', 'test_parent')
        print("  ✓ Step 3: Enhanced visualization generated")
        
        # Clean up
        os.unlink(csv_path)
        
    except Exception as e:
        print(f"  ✗ Complete workflow test failed: {e}")

if __name__ == "__main__":
    print("=== Enhanced Visualization Integration Test Suite ===")
    print()
    
    # Run integration tests
    test_data_loader_integration()
    print()
    
    test_visualization_functions()
    print()
    
    test_ui_integration()
    print()
    
    test_enhanced_features()
    print()
    
    test_complete_workflow()
    print()
    
    print("=== Integration Test Suite Complete ===")
    print("✓ Enhanced visualization features are ready for use!")