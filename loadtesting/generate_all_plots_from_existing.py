#!/usr/bin/env python3
"""
Generate comprehensive performance plots from existing Locust CSV data
====================================================================

This script finds your latest test results and generates multiple performance
plots showing how different metrics scale with user count across iterations:

- Average Response Time vs Users
- 95th Percentile Response Time vs Users  
- 99th Percentile Response Time vs Users
- Median Response Time vs Users
- Throughput (RPS) vs Users
- Error Rate vs Users
- Total Requests vs Users

Each plot shows 3 lines (one per iteration) similar to Locust's style.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
import re

def find_latest_reports_dir():
    """Find the most recent virtual_users directory"""
    reports_base = Path("loadtesting/reports")
    if not reports_base.exists():
        return None
    
    pattern = re.compile(r'virtual_users_(\d{8}_\d{6})')
    latest_dir = None
    latest_timestamp = ""
    
    for item in reports_base.iterdir():
        if item.is_dir():
            match = pattern.match(item.name)
            if match:
                timestamp = match.group(1)
                if timestamp > latest_timestamp:
                    latest_timestamp = timestamp
                    latest_dir = item
    
    return latest_dir

def parse_csv_data(reports_dir):
    """Parse all CSV files in the reports directory"""
    results = []
    
    for csv_file in reports_dir.glob("*_stats.csv"):
        # Extract user count and iteration from filename
        filename = csv_file.stem
        
        # Look for pattern like "Patient_management_workflow_5users_iter1_stats"
        user_match = re.search(r'(\d+)users', filename)
        iter_match = re.search(r'iter(\d+)', filename)
        
        if not user_match or not iter_match:
            continue
            
        user_count = int(user_match.group(1))
        iteration = int(iter_match.group(1))
            
        # Read CSV and find aggregated row
        try:
            df = pd.read_csv(csv_file)
            aggregated = df[df['Name'] == 'Aggregated']
            
            if aggregated.empty:
                # Sometimes the Aggregated row has an empty Name field
                potential_agg = df[df['Name'].isna() | (df['Name'] == '')]
                if not potential_agg.empty:
                    aggregated = potential_agg.iloc[-1:]
            
            if not aggregated.empty:
                row = aggregated.iloc[0]
                
                result = {
                    'user_count': user_count,
                    'iteration': iteration,
                    'avg_response_time': float(row['Average Response Time']),
                    'min_response_time': float(row['Min Response Time']), 
                    'max_response_time': float(row['Max Response Time']),
                    'median_response_time': float(row['Median Response Time']),
                    'percentile_95': float(row['95%']),
                    'percentile_99': float(row['99%']),
                    'requests_per_second': float(row['Requests/s']),
                    'failure_rate': (float(row['Failure Count']) / float(row['Request Count']) * 100) if float(row['Request Count']) > 0 else 0,
                    'total_requests': int(row['Request Count']),
                    'total_failures': int(row['Failure Count'])
                }
                results.append(result)
                
        except Exception as e:
            print(f"⚠️ Error parsing {csv_file}: {e}")
            continue
    
    return results

def create_metric_plot(results_df, metric_col, title, ylabel, filename, reports_dir):
    """Create a plot for any metric vs users with iteration lines"""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Set the style similar to Locust
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']  # Blue, Orange, Green
    
    # Plot each iteration as a separate line
    iterations = sorted(results_df['iteration'].unique())
    
    for i, iteration in enumerate(iterations):
        iter_data = results_df[results_df['iteration'] == iteration].sort_values('user_count')
        
        if not iter_data.empty:
            ax.plot(iter_data['user_count'], iter_data[metric_col], 
                   marker='o', linewidth=3, markersize=8, 
                   color=colors[i % len(colors)],
                   label=f'Iteration {iteration}')
            
            # Annotations removed for cleaner plots
    
    ax.set_xlabel('Number of Users', fontsize=12, fontweight='bold')
    ax.set_ylabel(ylabel, fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.legend(title='Iteration', loc='best', frameon=True, fancybox=True, shadow=True)
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Improve layout
    plt.tight_layout()
    
    # Save plot
    output_path = reports_dir / f"{filename}.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"📊 Generated: {filename}.png")

def generate_all_plots():
    """Generate all performance plots from existing CSV data"""
    
    # Find latest reports directory
    reports_dir = find_latest_reports_dir()
    if not reports_dir:
        print("❌ No reports directory found")
        return
    
    print(f"📁 Using reports directory: {reports_dir.name}")
    
    # Parse CSV data
    results = parse_csv_data(reports_dir)
    if not results:
        print("❌ No valid CSV data found")
        return
    
    print(f"📊 Found {len(results)} data points")
    
    # Convert to DataFrame
    df = pd.DataFrame(results)
    print(f"📈 User counts: {sorted(df['user_count'].unique())}")
    print(f"🔄 Iterations: {sorted(df['iteration'].unique())}")
    
    # Define all plots to generate
    plots = [
        ('avg_response_time', 'Average Response Time vs Users', 'Average Response Time (ms)', 'AvgResponseTime_vs_Users'),
        ('percentile_95', '95th Percentile Response Time vs Users', '95th Percentile Response Time (ms)', '95thPercentile_vs_Users'),
        ('percentile_99', '99th Percentile Response Time vs Users', '99th Percentile Response Time (ms)', '99thPercentile_vs_Users'),
        ('median_response_time', 'Median Response Time vs Users', 'Median Response Time (ms)', 'MedianResponseTime_vs_Users'),
        ('requests_per_second', 'Throughput (RPS) vs Users', 'Requests Per Second', 'Throughput_vs_Users'),
        ('failure_rate', 'Error Rate vs Users', 'Error Rate (%)', 'ErrorRate_vs_Users'),
        ('total_requests', 'Total Requests vs Users', 'Total Requests', 'TotalRequests_vs_Users')
    ]
    
    print(f"\\n🎨 Generating plots...")
    
    for metric_col, title, ylabel, filename in plots:
        if metric_col in df.columns:
            create_metric_plot(df, metric_col, title, ylabel, filename, reports_dir)
        else:
            print(f"⚠️ Skipping {title} - column {metric_col} not found")
    
    print(f"\\n🎉 All plots generated in: {reports_dir}")
    print("\\n📊 Generated plots:")
    for _, _, _, filename in plots:
        plot_path = reports_dir / f"{filename}.png"
        if plot_path.exists():
            print(f"   ✅ {filename}.png")

def main():
    """Main entry point"""
    print("🚀 Generating Performance Plots from Existing Data")
    print("=" * 55)
    
    generate_all_plots()
    
    return 0

if __name__ == "__main__":
    exit(main())