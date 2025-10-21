#!/usr/bin/env python3
"""
Virtual User Load Testing Launcher
=================================

Quick launcher for common OralSmart load testing scenarios.
Provides menu-driven interface for running load tests.
"""

import os
import subprocess
import sys
from pathlib import Path

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def run_test(scenario, users, host="http://localhost:8000"):
    """Run a virtual user load test"""
    script_path = Path(__file__).parent / "virtual_user_load_test.py"
    
    cmd = [
        sys.executable,
        str(script_path),
        "--scenario", scenario,
        "--users", str(users),
        "--host", host
    ]
    
    print(f"\\n🚀 Starting {scenario} with {users} virtual users...")
    print(f"📍 Target: {host}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd)
        return result.returncode == 0
    except KeyboardInterrupt:
        print("\\n⚠️ Test interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False

def main():
    """Main launcher interface"""
    
    scenarios = [
        ("Patient management workflow", 500),
        ("Patient management workflow", 1000),
        ("Assessment screening workflow", 500),
        ("Assessment screening workflow", 1000),
        ("Report generation stress test", 500),
        ("Report generation stress test", 1000),
        ("ML prediction performance test", 500),
        ("ML prediction performance test", 1000),
        ("Patient browsing and search", 500),
        ("Patient browsing and search", 1000),
        ("Clinic directory browsing", 500),
        ("Clinic directory browsing", 1000),
        ("Authentication load test", 500),
        ("Authentication load test", 1000),
        ("Mixed healthcare workflow", 500),
        ("Mixed healthcare workflow", 1000),
    ]
    
    while True:
        clear_screen()
        print("\\n" + "="*60)
        print("  🧪 OralSmart Virtual User Load Testing")
        print("="*60)
        print("\\nAvailable Test Scenarios:")
        print()
        
        for i, (scenario, users) in enumerate(scenarios, 1):
            print(f"  {i:2}. {scenario} - {users} virtual users")
        
        print(f"\\n  {len(scenarios)+1:2}. Custom scenario")
        print(f"  {len(scenarios)+2:2}. Exit")
        print()
        
        try:
            choice = input("Enter your choice: ").strip()
            
            if choice == str(len(scenarios) + 2):  # Exit
                print("\\n👋 Goodbye!")
                break
            
            elif choice == str(len(scenarios) + 1):  # Custom
                print()
                scenario = input("Enter scenario name: ").strip()
                if not scenario:
                    print("❌ Scenario name cannot be empty")
                    input("Press Enter to continue...")
                    continue
                
                try:
                    users = int(input("Enter number of virtual users: ").strip())
                    if users <= 0:
                        print("❌ Number of users must be positive")
                        input("Press Enter to continue...")
                        continue
                except ValueError:
                    print("❌ Invalid number of users")
                    input("Press Enter to continue...")
                    continue
                
                host = input("Enter target host (default: http://localhost:8000): ").strip()
                if not host:
                    host = "http://localhost:8000"
                
                success = run_test(scenario, users, host)
                
            else:
                try:
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(scenarios):
                        scenario, users = scenarios[choice_idx]
                        
                        host = input(f"Enter target host (default: http://localhost:8000): ").strip()
                        if not host:
                            host = "http://localhost:8000"
                        
                        success = run_test(scenario, users, host)
                    else:
                        print("❌ Invalid choice")
                        input("Press Enter to continue...")
                        continue
                except ValueError:
                    print("❌ Invalid choice")
                    input("Press Enter to continue...")
                    continue
            
            # Show results
            if 'success' in locals():
                print("\\n" + "="*60)
                if success:
                    print("✅ Test completed successfully!")
                else:
                    print("❌ Test failed or was interrupted")
                print("="*60)
                input("\\nPress Enter to return to menu...")
        
        except KeyboardInterrupt:
            print("\\n\\n⚠️ Interrupted by user")
            break
        except Exception as e:
            print(f"\\n❌ Unexpected error: {e}")
            input("Press Enter to continue...")

if __name__ == "__main__":
    main()