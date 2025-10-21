#!/usr/bin/env python3
"""
Simple Virtual User Load Test - No Heavy Dependencies
====================================================

A simplified version of the virtual user load test that doesn't require
matplotlib, seaborn, or other heavy dependencies. Focuses on running
tests and parsing results.

Usage:
    python loadtesting/simple_virtual_user_test.py --scenario "Patient management workflow" --users 50
"""

import os
import sys
import subprocess
import time
import json
from datetime import datetime
import argparse
from pathlib import Path

class SimpleVirtualUserLoadTester:
    """Simplified virtual user load testing without heavy dependencies"""
    
    def __init__(self, host="http://localhost:8000"):
        self.host = host
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.reports_dir = Path(__file__).parent / "reports" / f"simple_test_{self.timestamp}"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
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
        csv_prefix = self.reports_dir / f"{scenario_name.replace(' ', '_')}_{user_count}users_iter{iteration}"
        html_file = self.reports_dir / f"{scenario_name.replace(' ', '_')}_{user_count}users_iter{iteration}.html"
        
        # Build locust command
        cmd = [
            "locust",
            "-f", str(Path(__file__).parent / "locustfile.py"),
            "--host", self.host,
            "--users", str(user_count),
            "--spawn-rate", str(min(50, user_count // 10)),  # Reasonable spawn rate
            "--run-time", test_duration,
            "--headless",
            "--html", str(html_file),
            "--csv", str(csv_prefix),
            "--loglevel", "WARNING",
            "--stop-timeout", "60"  # Stop timeout to handle cleanup
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print(f"✅ Completed {scenario_name} - {user_count} virtual users - iteration {iteration}")
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
        """Parse Locust CSV stats file and extract metrics (simplified, no pandas)"""
        try:
            if not csv_file.exists():
                print(f"⚠️ CSV file not found: {csv_file}")
                return None
            
            import csv
            
            # Read CSV file properly using csv module
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            if len(rows) < 1:
                print(f"❌ CSV file is empty or has no data: {csv_file}")
                return None
            
            print(f"📊 CSV has {len(rows)} data rows")
            
            # Look for the Aggregated row
            aggregated_row = None
            for row in reversed(rows):  # Work backwards
                if row.get('Name') == 'Aggregated':
                    aggregated_row = row
                    break
            
            if not aggregated_row:
                print("❌ No aggregated row found in CSV")
                print("Available row names:", [row.get('Name', 'N/A') for row in rows[-5:]])  # Show last 5 rows
                return None
            
            print(f"📈 Found aggregated stats: {aggregated_row.get('Request Count', 'N/A')} requests, {aggregated_row.get('Failure Count', 'N/A')} failures")
            
            # Extract key metrics
            try:
                stats = {
                    'load_time': float(aggregated_row['Average Response Time']),
                    'latency': float(aggregated_row['95%']),
                    'connect_time': float(aggregated_row['Min Response Time']),
                    'requests_per_second': float(aggregated_row['Requests/s']),
                    'failure_rate': (float(aggregated_row['Failure Count']) / float(aggregated_row['Request Count']) * 100) if float(aggregated_row['Request Count']) > 0 else 0,
                    'total_requests': int(float(aggregated_row['Request Count']))
                }
                
                print(f"✅ Parsed stats: Load={stats['load_time']:.1f}ms, Latency={stats['latency']:.1f}ms, RPS={stats['requests_per_second']:.1f}")
                return stats
                
            except (ValueError, KeyError) as e:
                print(f"❌ Error parsing numeric values from CSV: {e}")
                print(f"Available fields: {list(aggregated_row.keys())}")
                print(f"Aggregated row data: {aggregated_row}")
                return None
            
        except Exception as e:
            print(f"❌ Error reading CSV {csv_file}: {e}")
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
                # Parse the results
                csv_file = self.reports_dir / f"{scenario_name.replace(' ', '_')}_{user_count}users_iter{iteration}_stats.csv"
                stats = self.parse_csv_stats(csv_file)
                
                if stats:
                    stats['iteration'] = iteration
                    results.append(stats)
                    print(f"📊 Iteration {iteration} results: {stats}")
                else:
                    print(f"⚠️ No stats extracted for iteration {iteration}")
            
            # Small delay between iterations
            time.sleep(2)
        
        return results
    
    def generate_simple_report(self, scenario_name, user_count, results):
        """Generate a simple text report without graphs"""
        if not results:
            print(f"No results to generate report for {scenario_name}")
            return
        
        report_file = self.reports_dir / f"Simple_Report_{user_count}_users_{scenario_name.replace(' ', '_')}.txt"
        
        with open(report_file, 'w') as f:
            f.write(f"OralSmart Load Testing Report\\n")
            f.write(f"================================\\n\\n")
            f.write(f"Scenario: {scenario_name}\\n")
            f.write(f"Virtual Users: {user_count}\\n")
            f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")
            f.write(f"Host: {self.host}\\n\\n")
            
            f.write(f"Results Summary:\\n")
            f.write(f"================\\n")
            
            total_requests = sum(r['total_requests'] for r in results)
            avg_load_time = sum(r['load_time'] for r in results) / len(results)
            avg_latency = sum(r['latency'] for r in results) / len(results)
            avg_rps = sum(r['requests_per_second'] for r in results) / len(results)
            avg_failure_rate = sum(r['failure_rate'] for r in results) / len(results)
            
            f.write(f"Total Requests: {total_requests}\\n")
            f.write(f"Average Load Time: {avg_load_time:.1f}ms\\n")
            f.write(f"Average Latency (95th percentile): {avg_latency:.1f}ms\\n")
            f.write(f"Average Requests/Second: {avg_rps:.1f}\\n")
            f.write(f"Average Failure Rate: {avg_failure_rate:.1f}%\\n\\n")
            
            f.write(f"Detailed Results by Iteration:\\n")
            f.write(f"==============================\\n")
            
            for result in results:
                f.write(f"Iteration {result['iteration']}:\\n")
                f.write(f"  Load Time: {result['load_time']:.1f}ms\\n")
                f.write(f"  Latency: {result['latency']:.1f}ms\\n")
                f.write(f"  Requests/Second: {result['requests_per_second']:.1f}\\n")
                f.write(f"  Failure Rate: {result['failure_rate']:.1f}%\\n")
                f.write(f"  Total Requests: {result['total_requests']}\\n\\n")
        
        print(f"📝 Simple Report saved: {report_file}")
    
    def run_complete_test(self, scenario_name, user_count):
        """Run complete test and generate simple report"""
        print(f"🚀 Starting Simple Virtual User Load Testing")
        print(f"📊 Scenario: {scenario_name}")
        print(f"👥 Virtual Users: {user_count}")
        print(f"🏠 Target Host: {self.host}")
        print(f"📁 Reports Directory: {self.reports_dir}")
        
        # Run the scenario test
        results = self.run_scenario_test(scenario_name, user_count)
        
        if results:
            # Generate simple report
            self.generate_simple_report(scenario_name, user_count, results)
            
            print(f"\\n🎉 Testing completed successfully!")
            print(f"📊 Report saved to: {self.reports_dir}")
            print(f"📈 {len(results)} successful iterations out of 3")
        else:
            print(f"\\n❌ No valid results obtained from testing")
            print(f"💡 Check the following:")
            print(f"   - Django server is running: python manage.py runserver")
            print(f"   - Server is accessible at: {self.host}")
            print(f"   - Locust is installed: pip install locust")
            print(f"   - No firewall issues")
        
        return results


def main():
    """Main entry point for simple virtual user load testing"""
    parser = argparse.ArgumentParser(description='Simple Virtual User Load Testing for OralSmart')
    parser.add_argument('--scenario', required=True, 
                       help='Test scenario name (e.g., "Preview asset test", "Browsing assets test")')
    parser.add_argument('--users', type=int, required=True,
                       help='Number of virtual users (e.g., 50, 100, 200)')
    parser.add_argument('--host', default='http://localhost:8000',
                       help='Target host for load testing (default: http://localhost:8000)')
    
    args = parser.parse_args()
    
    # Validate inputs
    if args.users <= 0:
        print("❌ Number of users must be positive")
        return 1
    
    # Initialize and run tests
    tester = SimpleVirtualUserLoadTester(host=args.host)
    
    try:
        results = tester.run_complete_test(args.scenario, args.users)
        return 0 if results else 1
    except KeyboardInterrupt:
        print("\\n⚠️ Testing interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Testing failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())