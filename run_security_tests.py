#!/usr/bin/env python
"""
Security Test Runner for OralSmart Application
Runs comprehensive security tests and generates reports
"""

import subprocess
import sys
import os
import argparse
from datetime import datetime

def run_command(command, capture_output=True):
    """Run a command and return the result."""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=capture_output, 
            text=True,
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def run_security_tests(test_categories=None, verbose=True, generate_report=True):
    """Run security tests based on categories."""
    
    print("🔐 OralSmart Security Test Suite")
    print("=" * 50)
    
    # Test categories
    all_categories = {
        'auth': 'test_security_auth.py',
        'csrf': 'test_security_csrf.py',
        'injection': 'test_security_injection.py',
        'access': 'test_security_access_control.py',
        'data': 'test_security_data_protection.py'
    }
    
    # Determine which tests to run
    if test_categories:
        categories_to_run = {k: v for k, v in all_categories.items() if k in test_categories}
    else:
        categories_to_run = all_categories
    
    results = {}
    
    # Run each test category
    for category, test_file in categories_to_run.items():
        print(f"\n📋 Running {category.upper()} security tests...")
        print("-" * 30)
        
        # Build pytest command
        cmd_parts = [
            "python -m pytest",
            f"tests/e2e/{test_file}",
            "-m security"
        ]
        
        if verbose:
            cmd_parts.append("-v")
        
        if generate_report:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = f"security_report_{category}_{timestamp}.html"
            cmd_parts.extend([
                "--html=" + report_file,
                "--self-contained-html"
            ])
        
        command = " ".join(cmd_parts)
        print(f"Running: {command}")
        
        # Execute test
        returncode, stdout, stderr = run_command(command, capture_output=True)
        
        results[category] = {
            'returncode': returncode,
            'stdout': stdout,
            'stderr': stderr
        }
        
        # Print results
        if returncode == 0:
            print(f"✅ {category.upper()} tests PASSED")
        else:
            print(f"❌ {category.upper()} tests FAILED")
        
        if verbose and stdout:
            print("STDOUT:")
            print(stdout)
        
        if stderr:
            print("STDERR:")
            print(stderr)
    
    # Summary
    print("\n" + "=" * 50)
    print("🏁 SECURITY TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for category, result in results.items():
        status = "PASSED" if result['returncode'] == 0 else "FAILED"
        status_emoji = "✅" if result['returncode'] == 0 else "❌"
        print(f"{status_emoji} {category.upper()}: {status}")
        
        if result['returncode'] == 0:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    
    return results

def run_security_scan():
    """Run additional security scans using external tools."""
    print("\n🔍 Running additional security scans...")
    
    # Check if common security tools are available
    security_tools = {
        'bandit': 'bandit -r src/ -f json -o security_bandit_report.json',
        'safety': 'safety check --json --output security_safety_report.json',
        'semgrep': 'semgrep --config=auto src/ --json -o security_semgrep_report.json'
    }
    
    for tool, command in security_tools.items():
        print(f"\nChecking for {tool}...")
        check_cmd = f"which {tool}" if os.name != 'nt' else f"where {tool}"
        returncode, _, _ = run_command(check_cmd)
        
        if returncode == 0:
            print(f"Running {tool} security scan...")
            run_command(command, capture_output=False)
        else:
            print(f"{tool} not installed. Install with: pip install {tool}")

def main():
    """Main function to parse arguments and run tests."""
    parser = argparse.ArgumentParser(
        description="Run security tests for OralSmart application"
    )
    
    parser.add_argument(
        '--categories', '-c',
        nargs='+',
        choices=['auth', 'csrf', 'injection', 'access', 'data'],
        help='Specific security test categories to run'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    parser.add_argument(
        '--no-report',
        action='store_true',
        help='Skip HTML report generation'
    )
    
    parser.add_argument(
        '--scan',
        action='store_true',
        help='Run additional security scans'
    )
    
    args = parser.parse_args()
    
    # Check if we're in the right directory
    if not os.path.exists('tests/e2e'):
        print("❌ Error: tests/e2e directory not found.")
        print("Please run this script from the project root directory.")
        sys.exit(1)
    
    # Run security tests
    results = run_security_tests(
        test_categories=args.categories,
        verbose=args.verbose,
        generate_report=not args.no_report
    )
    
    # Run additional security scans if requested
    if args.scan:
        run_security_scan()
    
    # Exit with appropriate code
    failed_tests = sum(1 for result in results.values() if result['returncode'] != 0)
    sys.exit(failed_tests)

if __name__ == "__main__":
    main()
