#!/usr/bin/env python3
"""
OralSmart Load Testing with Virtual User Scenarios
==================================================

This script provides load testing with specific virtual user scenarios:
- Load time reports with 500/1000 virtual users
- Latency reports with 500/1000 virtual users  
- Connect time reports with 500/1000 virtual users
- Each scenario runs 3 iterations for statistical accuracy

Usage:
    python loadtesting/virtual_user_load_test.py --scenario "Preview asset test" --users 500
    python loadtesting/virtual_user_load_test.py --scenario "Browsing assets test" --users 1000
"""

import os
import sys
import subprocess
import time
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import argparse
from pathlib import Path
import numpy as np

class VirtualUserLoadTester:
    """Manages virtual user load testing with specific scenarios"""
    
    def __init__(self, host="http://localhost:8000"):
        self.host = host
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.reports_dir = Path(__file__).parent / "reports" / f"virtual_users_{self.timestamp}"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Set style for graphs
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    def run_single_test(self, scenario_name, user_count, iteration, test_duration="2m"):
        """Run a single load test with specified virtual users"""
        
        print(f"🔄 Running {scenario_name} with {user_count} virtual users (iteration {iteration}/3)")
        
        # Test server connectivity first
        try:
            import requests
            response = requests.get(self.host, timeout=5)
            if response.status_code not in [200, 302]:
                print(f"⚠️ Server returned status {response.status_code}, continuing anyway...")
        except ImportError:
            print("⚠️ requests module not available, skipping connectivity test...")
        except Exception as e:
            if "Connection refused" in str(e) or "ConnectionError" in str(e):
                print(f"❌ Cannot connect to {self.host}")
                print("💡 Make sure Django server is running: python manage.py runserver")
                return False
            else:
                print(f"⚠️ Connection test failed: {e}, continuing anyway...")
        
        # Create unique filename for this test
        csv_prefix = str(self.reports_dir / f"{scenario_name.replace(' ', '_')}_{user_count}users_iter{iteration}")
        html_file = self.reports_dir / f"{scenario_name.replace(' ', '_')}_{user_count}users_iter{iteration}.html"
        
        # Build locust command
        cmd = [
            "locust",
            "-f", str(Path(__file__).parent / "locustfile.py"),
            "--host", self.host,
            "--users", str(user_count),
            "--spawn-rate", str(max(1, min(50, user_count // 10))),  # Reasonable spawn rate, min 1
            "--run-time", test_duration,
            "--headless",
            "--html", str(html_file),
            "--csv", str(csv_prefix),
            "--loglevel", "WARNING",
            "--stop-timeout", "60"  # Stop timeout to handle cleanup
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            # Check if CSV files were created (more reliable than exit code)
            expected_csv = self.reports_dir / f"{scenario_name.replace(' ', '_')}_{user_count}users_iter{iteration}_stats.csv"
            
            if result.returncode == 0 or expected_csv.exists():
                print(f"✅ Completed {scenario_name} - {user_count} virtual users - iteration {iteration}")
                if result.returncode != 0:
                    print(f"⚠️ Exit code {result.returncode} but CSV files were created successfully")
                return True
            else:
                print(f"❌ Failed {scenario_name} - {user_count} virtual users - iteration {iteration}")
                print(f"Error: {result.stderr}")
                # Check for common issues
                if "Connection refused" in result.stderr:
                    print("💡 Django server may not be running. Check: python manage.py runserver")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"⏱️ Timeout for {scenario_name} - {user_count} virtual users - iteration {iteration}")
            return False
        except Exception as e:
            print(f"💥 Exception in {scenario_name} - {user_count} virtual users - iteration {iteration}: {e}")
            return False
    
    def parse_csv_stats(self, csv_file):
        """Parse Locust CSV stats file and extract metrics"""
        try:
            print(f"🔍 Looking for CSV file: {csv_file}")
            if not csv_file.exists():
                print(f"⚠️ CSV file not found: {csv_file}")
                print(f"🗂️ Files in directory {csv_file.parent}:")
                if csv_file.parent.exists():
                    for f in csv_file.parent.iterdir():
                        print(f"  - {f.name}")
                return None
            
            df = pd.read_csv(csv_file)
            print(f"📊 Read CSV with {len(df)} rows")
            
            # Look for the Aggregated row (it may have an empty Name field)
            aggregated_row = df[df['Name'] == 'Aggregated']
            if aggregated_row.empty:
                # Sometimes the Aggregated row has an empty Name field
                # Look for rows where Name is NaN or empty, and it's the last meaningful row
                potential_agg = df[df['Name'].isna() | (df['Name'] == '')]
                if not potential_agg.empty:
                    aggregated_row = potential_agg.iloc[-1:]  # Take the last one
            
            if not aggregated_row.empty:
                # Use aggregated statistics
                row = aggregated_row.iloc[0]
                print(f"📈 Using aggregated stats: {row['Request Count']} requests, {row['Failure Count']} failures")
            else:
                # Fall back to calculating from individual requests
                print("📊 No aggregated row found, calculating from individual requests")
                df_filtered = df.dropna(subset=['Name'])
                if len(df_filtered) == 0:
                    print("❌ No valid request data found in CSV")
                    return None
                row = df_filtered  # Will calculate means below
            
            # Calculate metrics
            if not aggregated_row.empty:
                # Single aggregated row - get the actual values from the Series
                stats = {
                    'load_time': float(aggregated_row['Average Response Time'].iloc[0]),
                    'latency': float(aggregated_row['95%'].iloc[0]),
                    'connect_time': float(aggregated_row['Min Response Time'].iloc[0]),
                    'requests_per_second': float(aggregated_row['Requests/s'].iloc[0]),
                    'failure_rate': (float(aggregated_row['Failure Count'].iloc[0]) / float(aggregated_row['Request Count'].iloc[0]) * 100) if float(aggregated_row['Request Count'].iloc[0]) > 0 else 0,
                    'total_requests': int(aggregated_row['Request Count'].iloc[0])
                }
            else:
                # Multiple rows - calculate means
                df_filtered = df.dropna(subset=['Name'])
                if len(df_filtered) == 0:
                    print("❌ No valid request data found in CSV")
                    return None
                    
                stats = {
                    'load_time': float(df_filtered['Average Response Time'].mean()),
                    'latency': float(df_filtered['95%'].mean()),
                    'connect_time': float(df_filtered['Min Response Time'].mean()),
                    'requests_per_second': float(df_filtered['Requests/s'].sum()),
                    'failure_rate': (float(df_filtered['Failure Count'].sum()) / float(df_filtered['Request Count'].sum()) * 100) if float(df_filtered['Request Count'].sum()) > 0 else 0,
                    'total_requests': int(df_filtered['Request Count'].sum())
                }
            
            print(f"✅ Parsed stats: Load={stats['load_time']:.1f}ms, Latency={stats['latency']:.1f}ms, RPS={stats['requests_per_second']:.1f}")
            return stats
            
        except Exception as e:
            print(f"❌ Error parsing CSV {csv_file}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def run_scenario_test(self, scenario_name, user_count, iterations=3):
        """Run a complete scenario test with 3 iterations"""
        results = []
        
        print(f"\\n{'='*70}")
        print(f"🎯 {scenario_name.upper()} SCENARIO")
        print(f"👥 Virtual Users: {user_count}")
        print(f"🔄 Iterations: {iterations}")
        print(f"{'='*70}")
        
        for iteration in range(1, iterations + 1):
            success = self.run_single_test(scenario_name, user_count, iteration)
            
            if success:
                # Parse the results - Locust creates filename_stats.csv
                csv_file = self.reports_dir / f"{scenario_name.replace(' ', '_')}_{user_count}users_iter{iteration}_stats.csv"
                stats = self.parse_csv_stats(csv_file)
                
                if stats:
                    stats['iteration'] = iteration
                    results.append(stats)
            
            # Small delay between iterations
            time.sleep(2)
        
        return results
    
    def create_load_time_report(self, scenario_name, user_count, results):
        """Create Load Time Report"""
        if not results:
            print(f"No results to generate load time report for {scenario_name}")
            return
        
        df = pd.DataFrame(results)
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Plot load time for each iteration - convert to numpy arrays
        iterations = np.array(df['iteration'].tolist())
        load_times = np.array(df['load_time'].tolist())
        
        # Bar chart with error bars
        mean_load_time = float(np.mean(load_times))
        std_load_time = float(np.std(load_times))
        
        bars = ax.bar(iterations, load_times, alpha=0.7, color='skyblue', edgecolor='navy', linewidth=1.5)
        ax.axhline(y=mean_load_time, color='red', linestyle='--', linewidth=2, label=f'Average: {mean_load_time:.1f}ms')
        
        # Annotations
        for i, (iteration, load_time) in enumerate(zip(iterations, load_times)):
            ax.text(iteration, load_time + std_load_time * 0.1, f'{load_time:.1f}ms', 
                   ha='center', va='bottom', fontweight='bold')
        
        ax.set_xlabel('Iteration', fontsize=12, fontweight='bold')
        ax.set_ylabel('Load Time (ms)', fontsize=12, fontweight='bold')
        ax.set_title(f'Load Time Report with {user_count} Virtual Users\\n{scenario_name}', 
                    fontsize=14, fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Save the report
        report_file = self.reports_dir / f"Load_Time_Report_{user_count}_users_{scenario_name.replace(' ', '_')}.png"
        plt.savefig(report_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📊 Load Time Report saved: {report_file}")
    
    def create_latency_report(self, scenario_name, user_count, results):
        """Create Latency Report"""
        if not results:
            print(f"No results to generate latency report for {scenario_name}")
            return
        
        df = pd.DataFrame(results)
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Plot latency for each iteration - convert to numpy arrays
        iterations = np.array(df['iteration'].tolist())
        latencies = np.array(df['latency'].tolist())
        
        # Line plot with markers
        ax.plot(iterations, latencies, marker='o', linewidth=3, markersize=10, color='orange')
        
        # Fill area under the curve
        ax.fill_between(iterations, latencies, alpha=0.3, color='orange')
        
        # Add mean line
        mean_latency = float(np.mean(latencies))
        ax.axhline(y=mean_latency, color='red', linestyle='--', linewidth=2, label=f'Average: {mean_latency:.1f}ms')
        
        # Annotations
        for iteration, latency in zip(iterations, latencies):
            ax.annotate(f'{latency:.1f}ms', (iteration, latency), 
                       textcoords="offset points", xytext=(0,10), ha='center', fontweight='bold')
        
        ax.set_xlabel('Iteration', fontsize=12, fontweight='bold')
        ax.set_ylabel('Latency (ms)', fontsize=12, fontweight='bold')
        ax.set_title(f'Latency Report with {user_count} Virtual Users\\n{scenario_name}', 
                    fontsize=14, fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Save the report
        report_file = self.reports_dir / f"Latency_Report_{user_count}_users_{scenario_name.replace(' ', '_')}.png"
        plt.savefig(report_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📊 Latency Report saved: {report_file}")
    
    def create_connect_time_report(self, scenario_name, user_count, results):
        """Create Connect Time Report"""
        if not results:
            print(f"No results to generate connect time report for {scenario_name}")
            return
        
        df = pd.DataFrame(results)
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Plot connect time for each iteration - convert to numpy arrays
        iterations = np.array(df['iteration'].tolist())
        connect_times = np.array(df['connect_time'].tolist())
        
        # Scatter plot with trend line
        ax.scatter(iterations, connect_times, s=200, alpha=0.7, color='green', edgecolors='darkgreen', linewidth=2)
        
        # Add trend line
        z = np.polyfit(iterations, connect_times, 1)
        p = np.poly1d(z)
        ax.plot(iterations, p(iterations), "--", color='red', linewidth=2, label='Trend')
        
        # Add mean line
        mean_connect_time = float(np.mean(connect_times))
        ax.axhline(y=mean_connect_time, color='blue', linestyle='--', linewidth=2, label=f'Average: {mean_connect_time:.1f}ms')
        
        # Annotations
        for iteration, connect_time in zip(iterations, connect_times):
            ax.annotate(f'{connect_time:.1f}ms', (iteration, connect_time), 
                       textcoords="offset points", xytext=(0,15), ha='center', fontweight='bold')
        
        ax.set_xlabel('Iteration', fontsize=12, fontweight='bold')
        ax.set_ylabel('Connect Time (ms)', fontsize=12, fontweight='bold')
        ax.set_title(f'Connect Time Report with {user_count} Virtual Users\\n{scenario_name}', 
                    fontsize=14, fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Save the report
        report_file = self.reports_dir / f"Connect_Time_Report_{user_count}_users_{scenario_name.replace(' ', '_')}.png"
        plt.savefig(report_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📊 Connect Time Report saved: {report_file}")
    
    def generate_scaling_plots(self, scenario_name, results):
        """Generate plots showing response time vs number of users"""
        if not results:
            return
        
        df = pd.DataFrame(results)
        
        # Group by user count and iteration
        user_counts = sorted(df['user_count'].unique())
        iterations = sorted(df['iteration'].unique())
        
        # Create subplots for different metrics
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(f'Load Testing Scaling Analysis: {scenario_name}', fontsize=16, fontweight='bold')
        
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c']  # Blue, Orange, Green for iterations
        
        # Plot 1: Average Response Time vs Users
        for i, iteration in enumerate(iterations):
            iter_data = df[df['iteration'] == iteration]
            iter_data_grouped = iter_data.groupby('user_count')['load_time'].mean()
            ax1.plot(iter_data_grouped.index, iter_data_grouped.values, 
                    marker='o', linewidth=2, markersize=8, 
                    color=colors[i], label=f'Iteration {int(iteration)}')
        
        ax1.set_xlabel('Number of Users', fontweight='bold')
        ax1.set_ylabel('Average Response Time (ms)', fontweight='bold')
        ax1.set_title('Average Response Time vs User Count', fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Plot 2: 95th Percentile Latency vs Users
        for i, iteration in enumerate(iterations):
            iter_data = df[df['iteration'] == iteration]
            iter_data_grouped = iter_data.groupby('user_count')['latency'].mean()
            ax2.plot(iter_data_grouped.index, iter_data_grouped.values, 
                    marker='s', linewidth=2, markersize=8, 
                    color=colors[i], label=f'Iteration {int(iteration)}')
        
        ax2.set_xlabel('Number of Users', fontweight='bold')
        ax2.set_ylabel('95th Percentile Latency (ms)', fontweight='bold')
        ax2.set_title('95th Percentile Latency vs User Count', fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        # Plot 3: Requests per Second vs Users
        for i, iteration in enumerate(iterations):
            iter_data = df[df['iteration'] == iteration]
            iter_data_grouped = iter_data.groupby('user_count')['requests_per_second'].mean()
            ax3.plot(iter_data_grouped.index, iter_data_grouped.values, 
                    marker='^', linewidth=2, markersize=8, 
                    color=colors[i], label=f'Iteration {int(iteration)}')
        
        ax3.set_xlabel('Number of Users', fontweight='bold')
        ax3.set_ylabel('Requests per Second', fontweight='bold')
        ax3.set_title('Throughput vs User Count', fontweight='bold')
        ax3.grid(True, alpha=0.3)
        ax3.legend()
        
        # Plot 4: Failure Rate vs Users
        for i, iteration in enumerate(iterations):
            iter_data = df[df['iteration'] == iteration]
            iter_data_grouped = iter_data.groupby('user_count')['failure_rate'].mean()
            ax4.plot(iter_data_grouped.index, iter_data_grouped.values, 
                    marker='d', linewidth=2, markersize=8, 
                    color=colors[i], label=f'Iteration {int(iteration)}')
        
        ax4.set_xlabel('Number of Users', fontweight='bold')
        ax4.set_ylabel('Failure Rate (%)', fontweight='bold')
        ax4.set_title('Failure Rate vs User Count', fontweight='bold')
        ax4.grid(True, alpha=0.3)
        ax4.legend()
        
        plt.tight_layout()
        
        # Save the scaling analysis plot
        report_file = self.reports_dir / f"Scaling_Analysis_{scenario_name.replace(' ', '_')}.png"
        plt.savefig(report_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📊 Scaling Analysis Report saved: {report_file}")

    def create_response_time_vs_users_plot(self, scenario_name, results):
        """Create a dedicated plot: Response Time vs Number of Users with one line per iteration"""
        if not results:
            return

        df = pd.DataFrame(results)

        # Ensure user_count and iteration are numeric and sorted
        df['user_count'] = df['user_count'].astype(int)
        df['iteration'] = df['iteration'].astype(int)

        user_counts = sorted(df['user_count'].unique())
        iterations = sorted(df['iteration'].unique())

        fig, ax = plt.subplots(figsize=(12, 8))
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c']

        for i, iteration in enumerate(iterations):
            iter_data = df[df['iteration'] == iteration]
            # For each user count, take the average load_time for that iteration (should be one)
            grouped = iter_data.groupby('user_count')['load_time'].mean()
            # Only plot if we have data points
            if not grouped.empty:
                x_vals = list(grouped.index)
                y_vals = list(grouped.values)
                ax.plot(x_vals, y_vals, marker='o', linewidth=3, markersize=8, 
                       color=colors[i % len(colors)], label=f'Iteration {int(iteration)}')

        # Plot styling similar to Locust: lines, markers, grid
        ax.set_xlabel('Number of Users', fontsize=12, fontweight='bold')
        ax.set_ylabel('Average Response Time (ms)', fontsize=12, fontweight='bold')
        ax.set_title(f'Response Time vs Number of Users\n{scenario_name}', fontsize=14, fontweight='bold')
        ax.grid(True, which='both', linestyle='--', alpha=0.3)
        ax.legend(title='Iteration')

        # Annotations removed for cleaner plots

        plt.tight_layout()
        report_file = self.reports_dir / f"ResponseTime_vs_Users_{scenario_name.replace(' ', '_')}.png"
        plt.savefig(report_file, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"📊 Response Time vs Users plot saved: {report_file}")
    
    def generate_scaling_summary_report(self, scenario_name, user_counts, results):
        """Generate summary report for scaling test"""
        if not results:
            return
        
        df = pd.DataFrame(results)
        
        report_file = self.reports_dir / f"Scaling_Summary_{scenario_name.replace(' ', '_')}.md"
        
        with open(report_file, 'w') as f:
            f.write(f"# Scaling Test Report: {scenario_name}\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write(f"## Test Configuration\n")
            f.write(f"- **Scenario:** {scenario_name}\n")
            f.write(f"- **User Counts:** {user_counts}\n")
            f.write(f"- **Iterations per User Count:** 3\n")
            f.write(f"- **Target Host:** {self.host}\n\n")
            
            f.write(f"## Performance Summary by User Count\n\n")
            f.write(f"| Users | Avg Response Time (ms) | 95th Percentile (ms) | RPS | Failure Rate (%) |\n")
            f.write(f"|-------|----------------------|---------------------|-----|------------------|\n")
            
            for user_count in sorted(df['user_count'].unique()):
                user_data = df[df['user_count'] == user_count]
                avg_load_time = user_data['load_time'].mean()
                avg_latency = user_data['latency'].mean()
                avg_rps = user_data['requests_per_second'].mean()
                avg_failure_rate = user_data['failure_rate'].mean()
                
                f.write(f"| {int(user_count)} | {avg_load_time:.1f} | {avg_latency:.1f} | {avg_rps:.1f} | {avg_failure_rate:.1f} |\n")
            
            f.write(f"\n## Generated Reports\n")
            f.write(f"- Scaling Analysis: `Scaling_Analysis_{scenario_name.replace(' ', '_')}.png`\n")
        
        print(f"📝 Scaling Summary Report saved: {report_file}")
    
    def generate_summary_report(self, scenario_name, user_count, results):
        """Generate a comprehensive summary report"""
        if not results:
            return
        
        df = pd.DataFrame(results)
        
        report_file = self.reports_dir / f"Summary_Report_{user_count}_users_{scenario_name.replace(' ', '_')}.md"
        
        with open(report_file, 'w') as f:
            f.write(f"# {scenario_name} - {user_count} Virtual Users\\n\\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n\\n")
            
            f.write(f"## Test Configuration\\n")
            f.write(f"- **Scenario:** {scenario_name}\\n")
            f.write(f"- **Virtual Users:** {user_count}\\n")
            f.write(f"- **Iterations:** 3\\n")
            f.write(f"- **Target Host:** {self.host}\\n\\n")
            
            f.write(f"## Performance Metrics\\n\\n")
            f.write(f"| Iteration | Load Time (ms) | Latency (ms) | Connect Time (ms) | RPS | Failure Rate (%) |\\n")
            f.write(f"|-----------|----------------|--------------|-------------------|-----|------------------|\\n")
            
            for _, row in df.iterrows():
                f.write(f"| {row['iteration']} | {row['load_time']:.1f} | {row['latency']:.1f} | {row['connect_time']:.1f} | {row['requests_per_second']:.1f} | {row['failure_rate']:.1f} |\\n")
            
            # Calculate averages
            avg_load_time = df['load_time'].mean()
            avg_latency = df['latency'].mean()
            avg_connect_time = df['connect_time'].mean()
            avg_rps = df['requests_per_second'].mean()
            avg_failure_rate = df['failure_rate'].mean()
            
            f.write(f"| **Average** | **{avg_load_time:.1f}** | **{avg_latency:.1f}** | **{avg_connect_time:.1f}** | **{avg_rps:.1f}** | **{avg_failure_rate:.1f}** |\\n\\n")
            
            f.write(f"## Generated Reports\\n")
            f.write(f"- Load Time Report: `Load_Time_Report_{user_count}_users_{scenario_name.replace(' ', '_')}.png`\\n")
            f.write(f"- Latency Report: `Latency_Report_{user_count}_users_{scenario_name.replace(' ', '_')}.png`\\n")
            f.write(f"- Connect Time Report: `Connect_Time_Report_{user_count}_users_{scenario_name.replace(' ', '_')}.png`\\n")
        
        print(f"📝 Summary Report saved: {report_file}")
    
    def run_complete_test(self, scenario_name, user_count):
        """Run complete test and generate all reports"""
        print(f"🚀 Starting Virtual User Load Testing")
        print(f"📊 Scenario: {scenario_name}")
        print(f"👥 Virtual Users: {user_count}")
        print(f"🏠 Target Host: {self.host}")
        print(f"📁 Reports Directory: {self.reports_dir}")
        
        # Run the scenario test
        results = self.run_scenario_test(scenario_name, user_count)
        
        if results:
            # Generate all reports
            self.create_load_time_report(scenario_name, user_count, results)
            self.create_latency_report(scenario_name, user_count, results)
            self.create_connect_time_report(scenario_name, user_count, results)
            self.generate_summary_report(scenario_name, user_count, results)
            
            print(f"\\n🎉 Testing completed successfully!")
            print(f"📊 All reports saved to: {self.reports_dir}")
        else:
            print(f"\\n❌ No valid results obtained from testing")
        
        return results
    
    def run_scaling_test(self, scenario_name, user_counts):
        """Run load tests across multiple user counts and generate scaling plots"""
        all_results = []
        
        print(f"\n🚀 Starting Scaling Load Test")
        print(f"📊 Scenario: {scenario_name}")
        print(f"👥 User Counts: {user_counts}")
        print(f"🏠 Target Host: {self.host}")
        print(f"📁 Reports Directory: {self.reports_dir}")
        
        for user_count in user_counts:
            print(f"\n{'='*70}")
            print(f"🎯 Testing with {user_count} users")
            print(f"{'='*70}")
            
            results = self.run_scenario_test(scenario_name, user_count, iterations=3)
            if results:
                # Add user count to each result
                for result in results:
                    result['user_count'] = user_count
                all_results.extend(results)
            
            # Small delay between user count tests
            time.sleep(5)
        
        if all_results:
            self.generate_scaling_plots(scenario_name, all_results)
            # Additional plot: Response Time vs Users with one line per iteration
            self.create_response_time_vs_users_plot(scenario_name, all_results)
            self.generate_scaling_summary_report(scenario_name, user_counts, all_results)
            
            print(f"\n🎉 Scaling test completed successfully!")
            print(f"📊 All reports saved to: {self.reports_dir}")
        else:
            print(f"\n❌ No valid results obtained from scaling test")
        
        return all_results


def parse_user_range(user_range_str):
    """Parse user range string into list of user counts"""
    try:
        if ',' in user_range_str:
            # Comma-separated list: "1,5,10,15,20"
            return [int(x.strip()) for x in user_range_str.split(',') if x.strip()]
        elif '-' in user_range_str:
            # Range format: "5-25-5" (start-end-step)
            parts = user_range_str.split('-')
            if len(parts) == 3:
                start, end, step = map(int, parts)
                return list(range(start, end + 1, step))
        else:
            # Single number
            return [int(user_range_str)]
    except ValueError:
        return []
    return []


def main():
    """Main entry point for virtual user load testing"""
    parser = argparse.ArgumentParser(description='Virtual User Load Testing for OralSmart')
    parser.add_argument('--scenario', required=True, 
                       help='Test scenario name (e.g., "Preview asset test", "Browsing assets test")')
    parser.add_argument('--users', type=int,
                       help='Number of virtual users (e.g., 500, 1000)')
    parser.add_argument('--user-range', type=str,
                       help='Range of users to test (e.g., "1,5,10,15,20" or "5-25-5" for 5 to 25 step 5)')
    parser.add_argument('--host', default='http://localhost:8000',
                       help='Target host for load testing (default: http://localhost:8000)')
    
    args = parser.parse_args()
    
    # Validate inputs - either --users or --user-range must be provided
    if not args.users and not args.user_range:
        print("❌ Either --users or --user-range must be specified")
        return 1
    
    if args.users and args.user_range:
        print("❌ Cannot specify both --users and --user-range")
        return 1
    
    # Parse user counts
    if args.users:
        if args.users <= 0:
            print("❌ Number of users must be positive")
            return 1
        user_counts = [args.users]
    else:
        user_counts = parse_user_range(args.user_range)
        if not user_counts:
            print("❌ Invalid user range format")
            return 1
    
    # Initialize and run tests
    tester = VirtualUserLoadTester(host=args.host)
    
    try:
        if len(user_counts) == 1:
            results = tester.run_complete_test(args.scenario, user_counts[0])
            return 0 if results else 1
        else:
            results = tester.run_scaling_test(args.scenario, user_counts)
            return 0 if results else 1
    except KeyboardInterrupt:
        print("\\n⚠️ Testing interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Testing failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())