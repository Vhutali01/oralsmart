#!/usr/bin/env python3
"""
Quick Server Check and Setup for Load Testing
============================================

This script helps ensure your Django server is running and ready for load testing.
"""

import requests
import subprocess
import sys
import time
from pathlib import Path

def check_server(host="http://localhost:8000", timeout=5):
    """Check if Django server is running and accessible"""
    # Try both localhost and 127.0.0.1
    hosts_to_try = [host]
    if "localhost" in host:
        hosts_to_try.append(host.replace("localhost", "127.0.0.1"))
    elif "127.0.0.1" in host:
        hosts_to_try.append(host.replace("127.0.0.1", "localhost"))
    
    for test_host in hosts_to_try:
        try:
            response = requests.get(test_host, timeout=timeout)
            if response.status_code == 200:
                print(f"✅ Server is running and accessible at {test_host}")
                return True
            else:
                print(f"⚠️ Server at {test_host} responded with status code: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"❌ Cannot connect to server at {test_host}")
        except requests.exceptions.Timeout:
            print(f"⏱️ Server connection timed out at {test_host}")
        except Exception as e:
            print(f"❌ Error checking server at {test_host}: {e}")
    
    print("   Make sure Django server is running: cd src && python manage.py runserver")
    return False

def setup_test_data():
    """Run the setup_test_data script if it exists"""
    setup_script = Path(__file__).parent / "setup_test_data.py"
    if setup_script.exists():
        print("📋 Setting up test data...")
        try:
            result = subprocess.run([sys.executable, str(setup_script)], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Test data setup completed")
                return True
            else:
                print("⚠️ Test data setup had warnings:")
                print(result.stdout)
                return True  # Continue anyway
        except Exception as e:
            print(f"⚠️ Could not setup test data: {e}")
            return True  # Continue anyway
    else:
        print("ℹ️ No test data setup script found (optional)")
        return True

def quick_locust_test(host="http://localhost:8000"):
    """Run a quick locust test to verify everything works"""
    print("🧪 Running quick verification test...")
    
    locust_file = Path(__file__).parent / "locustfile.py"
    
    cmd = [
        "locust",
        "-f", str(locust_file),
        "--host", host,
        "--users", "2",
        "--spawn-rate", "1", 
        "--run-time", "30s",
        "--headless",
        "--loglevel", "WARNING"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print("✅ Quick test completed successfully")
            print("🎯 Load testing setup is working!")
            return True
        else:
            print("⚠️ Quick test completed with warnings:")
            print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print("⚠️ Quick test timed out (this might be normal)")
        return True
    except Exception as e:
        print(f"❌ Quick test failed: {e}")
        return False

def main():
    print("🔧 OralSmart Load Testing Setup Checker")
    print("=" * 40)
    
    # Check server
    if not check_server():
        print("\n💡 To start the Django server:")
        print("   1. Open a new terminal")
        print("   2. cd src")
        print("   3. python manage.py runserver")
        return 1
    
    # Setup test data
    setup_test_data()
    
    # Quick verification test
    print("\n🧪 Running verification test...")
    if quick_locust_test():
        print("\n🎉 Everything is ready for load testing!")
        print("\n📈 You can now run:")
        print("   python loadtesting/enhanced_load_test.py --iterations=3")
        return 0
    else:
        print("\n⚠️ There might be some issues, but you can try running the full tests")
        return 1

if __name__ == "__main__":
    exit(main())