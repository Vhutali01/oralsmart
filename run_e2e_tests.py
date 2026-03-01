#!/usr/bin/env python3
"""
End-to-End Test Runner for OralSmart Application

This script provides easy commands to run different test suites:
- Authentication tests
- Patient management tests  
- Assessment form tests
- ML prediction workflow tests
- Report generation tests
- File upload tests

Usage:
    python run_e2e_tests.py --all              # Run all E2E tests
    python run_e2e_tests.py --auth             # Run authentication tests only
    python run_e2e_tests.py --patient          # Run patient management tests
    python run_e2e_tests.py --assessment       # Run assessment form tests
    python run_e2e_tests.py --ml               # Run ML prediction tests
    python run_e2e_tests.py --reports          # Run report generation tests
    python run_e2e_tests.py --uploads          # Run file upload tests
    python run_e2e_tests.py --smoke            # Run smoke tests (key functionality)
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path

class E2ETestRunner:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.test_dir = self.base_dir / "tests" / "e2e"
        
        # Test configurations
        self.test_suites = {
            'auth': {
                'file': 'test_authentication.py',
                'description': 'User authentication and authorization tests'
            },
            'patient': {
                'file': 'test_patient_management.py', 
                'description': 'Patient registration and management tests'
            },
            'assessment': {
                'file': 'test_assessment_forms.py',
                'description': 'Assessment form completion tests'
            },
            'ml': {
                'file': 'test_ml_prediction.py',
                'description': 'ML risk prediction workflow tests'
            },
            'reports': {
                'file': 'test_report_generation.py',
                'description': 'Report generation tests'
            },
            'uploads': {
                'file': 'test_file_uploads.py',
                'description': 'File upload functionality tests'
            }
        }
        
        # Smoke tests - most critical functionality
        self.smoke_tests = [
            'tests/e2e/test_authentication.py::TestAuthentication::test_user_login_success',
            'tests/e2e/test_patient_management.py::TestPatientManagement::test_create_patient_success',
            'tests/e2e/test_assessment_forms.py::TestAssessmentForms::test_dental_screening_form_completion',
            'tests/e2e/test_ml_prediction.py::TestMLRiskPrediction::test_ml_prediction_after_complete_assessment',
            'tests/e2e/test_report_generation.py::TestReportGeneration::test_view_patient_report'
        ]
    
    def run_tests(self, test_type='all', browser='chromium', headless=False, verbose=False):
        """Run the specified test suite."""
        print(f"Running OralSmart E2E Tests - {test_type.upper()}")
        print(f"Browser: {browser}")
        print(f"Headless: {headless}")
        print("-" * 50)
        
        # Build pytest command - use sys.executable to get current Python interpreter
        cmd = [sys.executable, '-m', 'pytest']
        
        # Add verbosity
        if verbose:
            cmd.append('-v')
        else:
            cmd.append('-q')
        
        # Add browser selection
        cmd.extend(['--browser', browser])
        
        # Add headless mode
        if headless:
            cmd.append('--headed=false')
        else:
            cmd.append('--headed')
        
        # Add test markers for filtering
        if test_type == 'all':
            cmd.append('-m')
            cmd.append('e2e')
        elif test_type == 'smoke':
            cmd.extend(self.smoke_tests)
        elif test_type == 'custom':
            # Custom test files will be added by the caller
            pass
        elif test_type in self.test_suites:
            test_file = self.test_dir / self.test_suites[test_type]['file']
            cmd.append(str(test_file))
        else:
            print(f"Unknown test type: {test_type}")
            return False
        
        # Add output formatting
        cmd.extend([
            '--tb=short',
            '--no-header',
            '--disable-warnings'
        ])
        
        try:
            # Change to project directory
            os.chdir(self.base_dir)
            
            # Run tests
            result = subprocess.run(cmd, capture_output=False)
            
            if result.returncode == 0:
                print("\n✅ All tests passed!")
                return True
            else:
                print(f"\\nTests failed with return code: {result.returncode}")
                return False
                
        except FileNotFoundError:
            print("Error: pytest not found. Please install pytest: pip install pytest pytest-playwright")
            return False
        except Exception as e:
            print(f"Error running tests: {e}")
            return False
    
    def run_custom_tests(self, test_files, browser='chromium', headless=False, verbose=False):
        """Run custom test files."""
        print(f"🚀 Running Custom E2E Tests")
        print(f"Files: {test_files}")
        print(f"Browser: {browser}")
        print(f"Headless: {headless}")
        print("-" * 50)
        
        # Build pytest command - use sys.executable to get current Python interpreter
        cmd = [sys.executable, '-m', 'pytest']
        
        # Add verbosity
        if verbose:
            cmd.append('-v')
        else:
            cmd.append('-q')
        
        # Add browser selection
        cmd.extend(['--browser', browser])
        
        # Add headless mode
        if headless:
            cmd.append('--headed=false')
        else:
            cmd.append('--headed')
        
        # Add test files
        cmd.extend(test_files)
        
        # Add output formatting
        cmd.extend([
            '--tb=short',
            '--no-header',
            '--disable-warnings'
        ])
        
        try:
            # Change to project directory
            os.chdir(self.base_dir)
            
            # Run tests
            result = subprocess.run(cmd, capture_output=False)
            
            if result.returncode == 0:
                print("\n✅ All tests passed!")
                return True
            else:
                print(f"\n❌ Tests failed with return code: {result.returncode}")
                return False
                
        except Exception as e:
            print(f"❌ Error running tests: {e}")
            return False
    
    def list_tests(self):
        """List available test suites."""
        print("📋 Available Test Suites:")
        print("-" * 50)
        
        for name, config in self.test_suites.items():
            print(f"  {name:12} - {config['description']}")
        
        print(f"  {'smoke':12} - Critical functionality tests")
        print(f"  {'all':12} - Run all E2E tests")
    
    def setup_environment(self):
        """Setup test environment and dependencies."""
        print("🔧 Setting up E2E test environment...")
        
        # Check if required packages are installed
        required_packages = ['pytest', 'pytest-playwright', 'pytest-django', 'pillow']
        
        try:
            import pytest
            import playwright
            import PIL
            print("✅ Required packages are installed")
        except ImportError as e:
            print(f"❌ Missing package: {e.name}")
            print("Please install required packages:")
            print("pip install pytest pytest-playwright pytest-django pillow")
            return False
        
        # Install playwright browsers
        print("📥 Installing Playwright browsers...")
        try:
            subprocess.run([sys.executable, '-m', 'playwright', 'install'], check=True)
            print("✅ Playwright browsers installed")
        except subprocess.CalledProcessError:
            print("❌ Failed to install Playwright browsers")
            return False
        
        return True

def main():
    parser = argparse.ArgumentParser(
        description='OralSmart E2E Test Runner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--all', action='store_true',
        help='Run all E2E tests'
    )
    parser.add_argument(
        '--smoke', action='store_true', 
        help='Run smoke tests (critical functionality)'
    )
    parser.add_argument(
        '--auth', action='store_true',
        help='Run authentication tests'
    )
    parser.add_argument(
        '--patient', action='store_true',
        help='Run patient management tests'
    )
    parser.add_argument(
        '--assessment', action='store_true',
        help='Run assessment form tests'
    )
    parser.add_argument(
        '--ml', action='store_true',
        help='Run ML prediction tests'
    )
    parser.add_argument(
        '--reports', action='store_true',
        help='Run report generation tests'
    )
    parser.add_argument(
        '--uploads', action='store_true',
        help='Run file upload tests'
    )
    parser.add_argument(
        '--browser', choices=['chromium', 'firefox', 'webkit'],
        default='chromium', help='Browser to use for testing'
    )
    parser.add_argument(
        '--headless', action='store_true',
        help='Run tests in headless mode'
    )
    parser.add_argument(
        '--verbose', '-v', action='store_true',
        help='Verbose output'
    )
    parser.add_argument(
        '--list', action='store_true',
        help='List available test suites'
    )
    parser.add_argument(
        '--setup', action='store_true',
        help='Setup test environment and install dependencies'
    )
    parser.add_argument(
        'test_files', nargs='*',
        help='Specific test files to run (optional)'
    )
    
    args = parser.parse_args()
    
    runner = E2ETestRunner()
    
    if args.setup:
        return 0 if runner.setup_environment() else 1
    
    if args.list:
        runner.list_tests()
        return 0
    
    # Determine which test type to run
    test_type = 'all'  # default
    
    if args.test_files:
        test_type = 'custom'
    elif args.smoke:
        test_type = 'smoke'
    elif args.auth:
        test_type = 'auth'
    elif args.patient:
        test_type = 'patient'
    elif args.assessment:
        test_type = 'assessment'
    elif args.ml:
        test_type = 'ml'
    elif args.reports:
        test_type = 'reports'
    elif args.uploads:
        test_type = 'uploads'
    elif args.all:
        test_type = 'all'
    
    # Run tests
    success = runner.run_tests(
        test_type=test_type,
        browser=args.browser,
        headless=args.headless,
        verbose=args.verbose
    )
    
    # Add custom test files if specified
    if args.test_files and test_type == 'custom':
        success = runner.run_custom_tests(
            test_files=args.test_files,
            browser=args.browser,
            headless=args.headless,
            verbose=args.verbose
        )
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
