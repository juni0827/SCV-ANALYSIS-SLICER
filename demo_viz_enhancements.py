#!/usr/bin/env python3
"""
Demonstration script for enhanced visualization features
Creates sample plots to showcase the improvements
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import os

def create_demo_data():
    """Create interesting demo data"""
    np.random.seed(42)
    n = 2000
    
    # Create correlated data
    x = np.random.normal(100, 20, n)
    y = 2.5 * x + np.random.normal(0, 15, n)
    z = np.random.exponential(2, n)
    
    # Create categorical data with different distributions per category
    categories = np.random.choice(['Type A', 'Type B', 'Type C', 'Type D'], n, p=[0.4, 0.3, 0.2, 0.1])
    
    # Adjust numeric values based on category for interesting patterns
    x_adjusted = x.copy()
    x_adjusted[categories == 'Type B'] += 30
    x_adjusted[categories == 'Type C'] -= 20
    x_adjusted[categories == 'Type D'] += 50
    
    data = {
        'Sales': x_adjusted,
        'Revenue': y,
        'CustomerAge': np.random.normal(35, 12, n),
        'ProductType': categories,
        'Region': np.random.choice(['North', 'South', 'East', 'West'], n),
        'Date': pd.date_range('2023-01-01', periods=n, freq='D')
    }
    
    return pd.DataFrame(data)

def demo_basic_plots():
    """Demonstrate basic plot enhancements"""
    print("Creating basic plot demonstrations...")
    df = create_demo_data()
    
    # Create enhanced plots for different data types
    plot_types = ["Histogram", "Violin", "Density", "QQ Plot"]
    
    for plot_type in plot_types:
        plt.style.use("dark_background")
        fig, ax = plt.subplots(figsize=(8, 5), facecolor="#1a1a1a")
        
        # Simulate the enhanced plot_generic function behavior
        if plot_type == "Histogram":
            ax.hist(df['Sales'].dropna(), bins=30, alpha=0.8, color='#4ECDC4', 
                    edgecolor='#45B7D1', linewidth=0.5)
        elif plot_type == "Violin":
            parts = ax.violinplot([df['Sales'].dropna().values], positions=[1], showmeans=True, showmedians=True)
            for pc in parts['bodies']:
                pc.set_facecolor('#96CEB4')
                pc.set_alpha(0.7)
        elif plot_type == "Density":
            df['Sales'].dropna().plot.density(ax=ax, alpha=0.8, color='#FFEAA7', linewidth=2)
        elif plot_type == "QQ Plot":
            from scipy import stats
            stats.probplot(df['Sales'].dropna(), dist="norm", plot=ax)
        
        # Apply enhanced theming
        ax.set_facecolor("#1a1a1a")
        ax.set_title(f"Enhanced {plot_type}: Sales Data", fontsize=11, color='#CCCCCC', fontweight='bold')
        ax.tick_params(colors='#CCCCCC', labelsize=9)
        for spine in ax.spines.values():
            spine.set_color('#CCCCCC')
            spine.set_alpha(0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(True, color='#404040', alpha=0.3, linestyle='-', linewidth=0.5)
        
        plt.tight_layout()
        plt.savefig(f'/tmp/demo_{plot_type.lower().replace(" ", "_")}.png', 
                   facecolor='#1a1a1a', dpi=100, bbox_inches='tight')
        plt.close()
        print(f"  ✓ Created enhanced {plot_type} plot")

def demo_advanced_plots():
    """Demonstrate advanced plot features"""
    print("Creating advanced plot demonstrations...")
    df = create_demo_data()
    
    # 1. Enhanced regression plot
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(10, 6), facecolor="#1a1a1a")
    
    # Scatter plot with regression line
    ax.scatter(df['Sales'], df['Revenue'], alpha=0.6, color='#4ECDC4', s=25)
    
    # Calculate and plot regression line
    z = np.polyfit(df['Sales'], df['Revenue'], 1)
    p = np.poly1d(z)
    ax.plot(df['Sales'], p(df['Sales']), color='#FF6B6B', linewidth=2)
    
    # Calculate correlation
    corr = df['Sales'].corr(df['Revenue'])
    ax.text(0.05, 0.95, f'Correlation: {corr:.3f}', transform=ax.transAxes, 
            bbox=dict(boxstyle="round,pad=0.3", facecolor='#45B7D1', alpha=0.7),
            color='white', fontweight='bold')
    
    # Apply theming
    ax.set_facecolor("#1a1a1a")
    ax.set_title("Enhanced Regression Analysis: Sales vs Revenue", fontsize=11, color='#CCCCCC', fontweight='bold')
    ax.set_xlabel("Sales", color='#CCCCCC')
    ax.set_ylabel("Revenue", color='#CCCCCC')
    ax.tick_params(colors='#CCCCCC', labelsize=9)
    for spine in ax.spines.values():
        spine.set_color('#CCCCCC')
        spine.set_alpha(0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(True, color='#404040', alpha=0.3, linestyle='-', linewidth=0.5)
    
    plt.tight_layout()
    plt.savefig('/tmp/demo_regression.png', facecolor='#1a1a1a', dpi=100, bbox_inches='tight')
    plt.close()
    print("  ✓ Created enhanced regression plot")
    
    # 2. Enhanced distribution comparison
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(10, 6), facecolor="#1a1a1a")
    
    colors = ['#4ECDC4', '#FF6B6B', '#45B7D1', '#96CEB4']
    grouped_data = df.groupby('ProductType')['Sales']
    
    for i, (group, group_data) in enumerate(grouped_data):
        if len(group_data.dropna()) > 0:
            group_data.dropna().plot.density(ax=ax, alpha=0.7, label=str(group), 
                                   color=colors[i % len(colors)], linewidth=2)
    
    ax.legend(framealpha=0.9, facecolor='#2a2a2a', edgecolor='#CCCCCC')
    ax.set_facecolor("#1a1a1a")
    ax.set_title("Enhanced Distribution Comparison: Sales by Product Type", fontsize=11, color='#CCCCCC', fontweight='bold')
    ax.set_xlabel("Sales", color='#CCCCCC')
    ax.set_ylabel("Density", color='#CCCCCC')
    ax.tick_params(colors='#CCCCCC', labelsize=9)
    for spine in ax.spines.values():
        spine.set_color('#CCCCCC')
        spine.set_alpha(0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(True, color='#404040', alpha=0.3, linestyle='-', linewidth=0.5)
    
    plt.tight_layout()
    plt.savefig('/tmp/demo_distribution_comparison.png', facecolor='#1a1a1a', dpi=100, bbox_inches='tight')
    plt.close()
    print("  ✓ Created enhanced distribution comparison plot")

def show_color_palette():
    """Demonstrate the enhanced color palette"""
    print("Creating color palette demonstration...")
    
    colors = ['#4ECDC4', '#FF6B6B', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98FB98', '#F0E68C']
    color_names = ['Primary', 'Secondary', 'Accent', 'Success', 'Warning', 'Light', 'Green', 'Yellow']
    
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(12, 3), facecolor="#1a1a1a")
    
    for i, (color, name) in enumerate(zip(colors, color_names)):
        ax.bar(i, 1, color=color, alpha=0.8, edgecolor='white', linewidth=1)
        ax.text(i, 0.5, name, ha='center', va='center', rotation=90, 
                color='white', fontweight='bold', fontsize=9)
    
    ax.set_facecolor("#1a1a1a")
    ax.set_title("Enhanced Color Palette for Dark Theme", fontsize=14, color='#CCCCCC', fontweight='bold')
    ax.set_xlim(-0.5, len(colors)-0.5)
    ax.set_ylim(0, 1)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    
    plt.tight_layout()
    plt.savefig('/tmp/demo_color_palette.png', facecolor='#1a1a1a', dpi=100, bbox_inches='tight')
    plt.close()
    print("  ✓ Created color palette demonstration")

if __name__ == "__main__":
    print("=== Enhanced Visualization Demonstration ===")
    
    # Create output directory
    os.makedirs('/tmp', exist_ok=True)
    
    # Run demonstrations
    demo_basic_plots()
    print()
    demo_advanced_plots()
    print()
    show_color_palette()
    print()
    
    print("=== Demonstration Complete ===")
    print("Generated demonstration plots in /tmp/")
    print("Available files:")
    for file in os.listdir('/tmp'):
        if file.startswith('demo_') and file.endswith('.png'):
            print(f"  - {file}")