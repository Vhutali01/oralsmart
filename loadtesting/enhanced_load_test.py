#!/usr/bin/env python3
"""
Enhanced Load Testing with Graphing for OralSmart
================================================

This script provides advanced load testing capabilities with detailed graphing.
It runs multiple test scenarios with different user loads and generates graphs
showing response time vs number of concurrent users.

Features:
- Configurable number of iterations
- Multiple scenarios (light, moderate, heavy load)
- Response time vs user count graphs for each scenario
- Detailed CSV reports
- Summary statistics
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

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

class LoadTestGraphGenerator:
    """Manages load testing execution and graph generation"""
    
    def __init__(self, host="http://localhost:8000", iterations=3):
        self.host = host
        self.iterations = iterations
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.reports_dir = Path(__file__).parent / "reports" / f"test_run_{self.timestamp}"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Test scenarios with different user loads
        self.scenarios = {
            "quick_test": {
                "users": [1, 3, 5],
                "spawn_rate": 2,
                "run_time": "30s",
                "description": "Quick Test (30 seconds each)"
            },
            "light_load": {
                "users": [1, 3, 5, 8, 10],
                "spawn_rate": 1,
                "run_time": "3m",
                "description": "Light Load (Browsing/Reading)"
            },
            "moderate_load": {
                "users": [10, 15, 20, 25, 30],
                "spawn_rate": 2,
                "run_time": "3m",
                "description": "Moderate Load (Normal Operations)"
            },
            "heavy_load": {
                "users": [20, 30, 40, 50, 60],
                "spawn_rate": 3,
                "run_time": "4m",
                "description": "Heavy Load (Intensive Operations)"
            }
        }
        
        # Set style for graphs
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    def run_single_test(self, scenario_name, user_count, iteration):
        """Run a single load test with specified parameters"""
        scenario = self.scenarios[scenario_name]
        
        # Create unique filename for this test
        csv_prefix = self.reports_dir / f"{scenario_name}_{user_count}users_iter{iteration}"
        html_file = self.reports_dir / f"{scenario_name}_{user_count}users_iter{iteration}.html"
        
        print(f"Running {scenario_name} with {user_count} users (iteration {iteration}/{self.iterations})")
        
        # Build locust command
        cmd = [
            "locust",
            "-f", str(Path(__file__).parent / "locustfile.py"),
            "--host", self.host,
            "--users", str(user_count),
            "--spawn-rate", str(scenario["spawn_rate"]),
            "--run-time", scenario["run_time"],
            "--headless",  # Run without web UI
            "--html", str(html_file),
            "--csv", str(csv_prefix),
            "--loglevel", "WARNING"  # Reduce log noise
        ]
        
        # Set timeout for the test
        timeout_seconds = 600  # 10 minutes timeout
        
        try:
            # Run the test
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_seconds)
            
            if result.returncode == 0:
                print(f"✓ Completed {scenario_name} - {user_count} users - iteration {iteration}")
                return True
            else:
                print(f"✗ Failed {scenario_name} - {user_count} users - iteration {iteration}")
                print(f"Error: {result.stderr}")
                if result.stdout:
                    print(f"Output: {result.stdout}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"⚠ Timeout for {scenario_name} - {user_count} users - iteration {iteration} (exceeded {timeout_seconds}s)")
            return False
        except Exception as e:
            print(f"✗ Exception in {scenario_name} - {user_count} users - iteration {iteration}: {e}")
            return False
    
    def parse_csv_stats(self, csv_file):
        """Parse Locust CSV stats file and extract key metrics"""
        try:
            if not csv_file.exists():
                return None
            
            df = pd.read_csv(csv_file)
            
            # Filter out aggregate rows and empty rows
            df = df[df['Name'] != 'Aggregated'].dropna(subset=['Name'])
            
            if len(df) == 0:
                print(f"Warning: No valid data in CSV {csv_file}")
                return None
            
            # Calculate overall metrics using correct column names
            stats = {
                'avg_response_time': df['Average Response Time'].mean(),
                'median_response_time': df['Median Response Time'].median(),
                'p95_response_time': df['95%'].mean(),
                'p99_response_time': df['99%'].mean(),
                'requests_per_second': df['Requests/s'].sum(),
                'failure_rate': (df['Failure Count'].sum() / df['Request Count'].sum() * 100) if df['Request Count'].sum() > 0 else 0,
                'total_requests': df['Request Count'].sum()
            }
            
            return stats
        except Exception as e:
            print(f"Error parsing CSV {csv_file}: {e}")
            # Print column names for debugging
            try:
                df = pd.read_csv(csv_file)
                print(f"Available columns: {df.columns.tolist()}")
            except:
                pass
            return None
    
    def run_scenario_tests(self, scenario_name):
        """Run all tests for a specific scenario"""
        scenario = self.scenarios[scenario_name]
        results = []
        
        print(f"\n{'='*50}")
        print(f"Running scenario: {scenario['description']}")
        print(f"{'='*50}")
        
        for user_count in scenario['users']:
            iteration_results = []
            
            for iteration in range(1, self.iterations + 1):
                success = self.run_single_test(scenario_name, user_count, iteration)
                
                if success:
                    # Parse the results
                    csv_file = self.reports_dir / f"{scenario_name}_{user_count}users_iter{iteration}_stats.csv"
                    stats = self.parse_csv_stats(csv_file)
                    
                    if stats:
                        stats['users'] = user_count
                        stats['iteration'] = iteration
                        iteration_results.append(stats)
                
                # Small delay between iterations
                time.sleep(2)
            
            if iteration_results:
                results.extend(iteration_results)
        
        return results
    
    def create_scenario_graph(self, scenario_name, results):
        """Create response time vs users graph for a scenario"""
        if not results:
            print(f"No results to graph for {scenario_name}")
            return
        
        df = pd.DataFrame(results)
        
        # Create figure with subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        
        # Graph 1: Average Response Time vs Users
        user_groups = df.groupby('users')['avg_response_time']
        users = user_groups.mean().index
        avg_times = user_groups.mean().values
        std_times = user_groups.std().values
        
        ax1.errorbar(users, avg_times, yerr=std_times, marker='o', capsize=5, capthick=2)
        ax1.set_xlabel('Number of Concurrent Users')
        ax1.set_ylabel('Average Response Time (ms)')
        ax1.set_title(f'{self.scenarios[scenario_name]["description"]} - Average Response Time')
        ax1.grid(True, alpha=0.3)
        
        # Graph 2: P95 Response Time vs Users
        p95_groups = df.groupby('users')['p95_response_time']
        p95_avg = p95_groups.mean().values
        p95_std = p95_groups.std().values
        
        ax2.errorbar(users, p95_avg, yerr=p95_std, marker='s', capsize=5, capthick=2, color='orange')
        ax2.set_xlabel('Number of Concurrent Users')
        ax2.set_ylabel('95th Percentile Response Time (ms)')
        ax2.set_title(f'{self.scenarios[scenario_name]["description"]} - P95 Response Time')
        ax2.grid(True, alpha=0.3)
        
        # Graph 3: Requests per Second vs Users
        rps_groups = df.groupby('users')['requests_per_second']
        rps_avg = rps_groups.mean().values
        rps_std = rps_groups.std().values
        
        ax3.errorbar(users, rps_avg, yerr=rps_std, marker='^', capsize=5, capthick=2, color='green')
        ax3.set_xlabel('Number of Concurrent Users')
        ax3.set_ylabel('Requests per Second')
        ax3.set_title(f'{self.scenarios[scenario_name]["description"]} - Throughput')
        ax3.grid(True, alpha=0.3)
        
        # Graph 4: Failure Rate vs Users
        failure_groups = df.groupby('users')['failure_rate']
        failure_avg = failure_groups.mean().values
        failure_std = failure_groups.std().values
        
        ax4.errorbar(users, failure_avg, yerr=failure_std, marker='d', capsize=5, capthick=2, color='red')
        ax4.set_xlabel('Number of Concurrent Users')
        ax4.set_ylabel('Failure Rate (%)')
        ax4.set_title(f'{self.scenarios[scenario_name]["description"]} - Failure Rate')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save the graph
        graph_file = self.reports_dir / f"{scenario_name}_performance_graphs.png"
        plt.savefig(graph_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ Graph saved: {graph_file}")
        
        # Also create individual detailed graphs
        self.create_detailed_response_time_graph(scenario_name, df)
    
    def create_detailed_response_time_graph(self, scenario_name, df):
        """Create detailed response time graph with all iterations visible"""
        plt.figure(figsize=(12, 8))
        
        # Plot each iteration as a separate line
        for iteration in df['iteration'].unique():
            iter_data = df[df['iteration'] == iteration]
            plt.plot(iter_data['users'], iter_data['avg_response_time'], 
                    marker='o', label=f'Iteration {iteration}', alpha=0.7, linewidth=2)
        
        # Calculate and plot the mean line
        mean_data = df.groupby('users')['avg_response_time'].mean()
        plt.plot(mean_data.index, mean_data.values, 
                marker='s', label='Average', color='black', linewidth=3, markersize=8)
        
        plt.xlabel('Number of Concurrent Users', fontsize=12)
        plt.ylabel('Average Response Time (ms)', fontsize=12)
        plt.title(f'{self.scenarios[scenario_name]["description"]}\nResponse Time vs Users ({self.iterations} iterations)', 
                 fontsize=14, fontweight='bold')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, alpha=0.3)
        
        # Add annotations for key points
        max_users = mean_data.index.max()
        max_response_time = mean_data.loc[max_users]
        plt.annotate(f'Max Load: {max_response_time:.1f}ms @ {max_users} users',
                    xy=(max_users, max_response_time),
                    xytext=(max_users * 0.7, max_response_time * 1.2),
                    arrowprops=dict(arrowstyle='->', color='red', lw=2),
                    fontsize=10, fontweight='bold')
        
        plt.tight_layout()
        
        # Save detailed graph
        detailed_graph_file = self.reports_dir / f"{scenario_name}_detailed_response_times.png"
        plt.savefig(detailed_graph_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ Detailed graph saved: {detailed_graph_file}")
    
    def create_summary_comparison(self, all_results):
        """Create a comparison graph across all scenarios"""
        if not all_results:
            return
        
        plt.figure(figsize=(14, 10))
        
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
        
        for idx, (scenario_name, results) in enumerate(all_results.items()):
            if not results:
                continue
            
            df = pd.DataFrame(results)
            mean_data = df.groupby('users')['avg_response_time'].mean()
            std_data = df.groupby('users')['avg_response_time'].std().fillna(0)
            
            # Ensure arrays are plain numpy floats for matplotlib (avoid pandas ExtensionArray typing issues)
            x = np.asarray(mean_data.index)
            y = mean_data.to_numpy(dtype=float)
            yerr = std_data.to_numpy(dtype=float)
            
            plt.errorbar(x, y, yerr=yerr,
                        label=self.scenarios[scenario_name]["description"],
                        marker='o', capsize=5, capthick=2, linewidth=2,
                        color=colors[idx % len(colors)])
        
        plt.xlabel('Number of Concurrent Users', fontsize=12)
        plt.ylabel('Average Response Time (ms)', fontsize=12)
        plt.title(f'OralSmart Load Testing Comparison\n({self.iterations} iterations per scenario)', 
                 fontsize=14, fontweight='bold')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Save comparison graph
        comparison_file = self.reports_dir / "scenarios_comparison.png"
        plt.savefig(comparison_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✓ Comparison graph saved: {comparison_file}")
    
    def generate_summary_report(self, all_results):
        """Generate a comprehensive summary report"""
        report_file = self.reports_dir / "load_test_summary.md"
        
        with open(report_file, 'w') as f:
            f.write(f"# OralSmart Load Testing Summary Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Test Configuration:**\n")
            f.write(f"- Target Host: {self.host}\n")
            f.write(f"- Iterations per scenario: {self.iterations}\n\n")
            
            for scenario_name, results in all_results.items():
                if not results:
                    continue
                
                df = pd.DataFrame(results)
                f.write(f"## {self.scenarios[scenario_name]['description']}\n\n")
                
                # Summary statistics
                summary_stats = df.groupby('users').agg({
                    'avg_response_time': ['mean', 'std'],
                    'p95_response_time': ['mean', 'std'],
                    'requests_per_second': ['mean', 'std'],
                    'failure_rate': ['mean', 'std']
                }).round(2)
                
                f.write("### Performance Summary\n\n")
                f.write("| Users | Avg Response Time (ms) | P95 Response Time (ms) | RPS | Failure Rate (%) |\n")
                f.write("|-------|----------------------|----------------------|-----|------------------|\n")
                
                for users in summary_stats.index:
                    avg_rt = summary_stats.loc[users, ('avg_response_time', 'mean')]
                    avg_rt_std = summary_stats.loc[users, ('avg_response_time', 'std')]
                    p95_rt = summary_stats.loc[users, ('p95_response_time', 'mean')]
                    rps = summary_stats.loc[users, ('requests_per_second', 'mean')]
                    failure_rate = summary_stats.loc[users, ('failure_rate', 'mean')]
                    
                    f.write(f"| {users} | {avg_rt:.1f} ± {avg_rt_std:.1f} | {p95_rt:.1f} | {rps:.1f} | {failure_rate:.1f} |\n")
                
                f.write(f"\n### Graphs\n")
                f.write(f"- Performance Overview: `{scenario_name}_performance_graphs.png`\n")
                f.write(f"- Detailed Response Times: `{scenario_name}_detailed_response_times.png`\n\n")
        
        print(f"✓ Summary report saved: {report_file}")
    
    def run_all_tests(self, scenarios=None):
        """Run all load testing scenarios"""
        if scenarios is None:
            scenarios = list(self.scenarios.keys())
        
        all_results = {}
        
        print(f"Starting load testing with {self.iterations} iterations per scenario")
        print(f"Target host: {self.host}")
        print(f"Reports will be saved to: {self.reports_dir}")
        
        for scenario_name in scenarios:
            if scenario_name not in self.scenarios:
                print(f"⚠ Unknown scenario: {scenario_name}")
                continue
            
            results = self.run_scenario_tests(scenario_name)
            all_results[scenario_name] = results
            
            if results:
                self.create_scenario_graph(scenario_name, results)
        
        # Create comparison graphs and reports
        self.create_summary_comparison(all_results)
        self.generate_summary_report(all_results)
        
        print(f"\n{'='*60}")
        print("🎉 Load testing completed successfully!")
        print(f"📊 Results available in: {self.reports_dir}")
        print(f"{'='*60}")
        
        return all_results


def main():
    """Main entry point for the load testing script"""
    parser = argparse.ArgumentParser(description='Enhanced Load Testing with Graphing for OralSmart')
    parser.add_argument('--host', default='http://localhost:8000', 
                       help='Target host for load testing (default: http://localhost:8000)')
    parser.add_argument('--iterations', type=int, default=3,
                       help='Number of iterations per scenario (default: 3)')
    parser.add_argument('--scenarios', nargs='+', 
                       choices=['quick_test', 'light_load', 'moderate_load', 'heavy_load'],
                       help='Specific scenarios to run (default: all)')
    parser.add_argument('--check-server', action='store_true',
                       help='Check if server is running before starting tests')
    
    args = parser.parse_args()
    
    # Check if server is running
    if args.check_server:
        import requests
        try:
            response = requests.get(args.host, timeout=5)
            print(f"✓ Server is running at {args.host}")
        except requests.exceptions.RequestException:
            print(f"✗ Server is not accessible at {args.host}")
            print("Please start the Django development server first:")
            print("cd src && python manage.py runserver")
            return 1
    
    # Initialize and run tests
    tester = LoadTestGraphGenerator(host=args.host, iterations=args.iterations)
    
    try:
        results = tester.run_all_tests(scenarios=args.scenarios)
        return 0
    except KeyboardInterrupt:
        print("\n⚠ Testing interrupted by user")
        return 1
    except Exception as e:
        print(f"✗ Testing failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())