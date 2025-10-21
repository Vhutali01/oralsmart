#!/usr/bin/env python3
"""
Django Server Connectivity Test
==============================

This script checks if the Django server is running and accessible
before running load tests.
"""

import requests
import sys
import time
from urllib.parse import urljoin

def test_server_connectivity(host="http://localhost:8000", timeout=5):
    """Test if Django server is running and accessible"""
    
    print(f"🔍 Testing connectivity to {host}")
    print("=" * 50)
    
    # List of endpoints to test
    test_endpoints = [
        "/",  # Landing page
        "/home/",  # Home page (may redirect to login)
        "/login_user/",  # Login page
        "/patient_list/",  # Patient list (may redirect to login)
        "/clinics/",  # Clinics page (may redirect to login)
        "/ml/model-status/",  # ML model status
    ]
    
    results = []
    
    for endpoint in test_endpoints:
        url = urljoin(host, endpoint)
        
        try:
            print(f"Testing {endpoint:<20} ... ", end="")
            response = requests.get(url, timeout=timeout, allow_redirects=True)
            
            if response.status_code == 200:
                print("✅ OK")
                results.append((endpoint, "OK", response.status_code))
            elif response.status_code in [301, 302]:
                print(f"🔄 Redirect ({response.status_code})")
                results.append((endpoint, "Redirect", response.status_code))
            elif response.status_code == 404:
                print(f"❌ Not Found ({response.status_code})")
                results.append((endpoint, "Not Found", response.status_code))
            else:
                print(f"⚠️ Status {response.status_code}")
                results.append((endpoint, f"Status {response.status_code}", response.status_code))
                
        except requests.exceptions.ConnectionError:
            print("❌ Connection Refused")
            results.append((endpoint, "Connection Refused", None))
        except requests.exceptions.Timeout:
            print("❌ Timeout")
            results.append((endpoint, "Timeout", None))
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append((endpoint, f"Error: {e}", None))
    
    print("\\n" + "=" * 50)
    print("CONNECTIVITY TEST SUMMARY")
    print("=" * 50)
    
    success_count = 0
    redirect_count = 0
    error_count = 0
    
    for endpoint, status, code in results:
        if status == "OK":
            success_count += 1
        elif status == "Redirect":
            redirect_count += 1
        else:
            error_count += 1
        
        print(f"{endpoint:<25} {status:<20} {code if code else 'N/A'}")
    
    print("\\n" + "-" * 50)
    print(f"✅ Success: {success_count}")
    print(f"🔄 Redirects: {redirect_count}")
    print(f"❌ Errors: {error_count}")
    
    # Overall assessment
    if error_count == 0:
        print("\\n🎉 Server is running and all endpoints are accessible!")
        return True
    elif success_count + redirect_count > error_count:
        print("\\n⚠️ Server is running but some endpoints have issues.")
        print("   This is normal if authentication is required.")
        return True
    else:
        print("\\n❌ Server appears to have connectivity issues.")
        return False

def test_django_specific_features(host="http://localhost:8000"):
    """Test Django-specific features"""
    
    print("\\n🔧 Testing Django-specific features...")
    print("=" * 50)
    
    # Test static files
    try:
        print("Static files ... ", end="")
        response = requests.get(f"{host}/static/css/style.css", timeout=5)
        if response.status_code == 200:
            print("✅ Available")
        else:
            print(f"⚠️ Status {response.status_code}")
    except:
        print("❌ Not accessible")
    
    # Test admin interface
    try:
        print("Admin interface ... ", end="")
        response = requests.get(f"{host}/admin/", timeout=5)
        if response.status_code in [200, 302]:
            print("✅ Available")
        else:
            print(f"⚠️ Status {response.status_code}")
    except:
        print("❌ Not accessible")
    
    # Test CSRF token availability
    try:
        print("CSRF tokens ... ", end="")
        response = requests.get(f"{host}/login_user/", timeout=5)
        if response.status_code == 200 and 'csrfmiddlewaretoken' in response.text:
            print("✅ Available")
        else:
            print("⚠️ May not be available")
    except:
        print("❌ Cannot check")

def main():
    """Main connectivity test function"""
    
    print("\\n🚀 Django Server Connectivity Test")
    print("=" * 60)
    
    # Allow custom host
    host = "http://localhost:8000"
    if len(sys.argv) > 1:
        host = sys.argv[1]
    
    # Basic connectivity test
    server_ok = test_server_connectivity(host)
    
    if server_ok:
        # Django-specific tests
        test_django_specific_features(host)
        
        print("\\n📋 RECOMMENDATIONS FOR LOAD TESTING:")
        print("=" * 50)
        print("1. ✅ Server is accessible - you can run load tests")
        print("2. 🔧 Use scenarios that match existing endpoints")
        print("3. 📊 Monitor server resources during testing")
        print("4. ⚠️ Some 404 errors are normal for non-existent patients/assessments")
        print("\\n🎯 Ready for load testing!")
        
        return 0
    else:
        print("\\n🚨 SERVER ISSUES DETECTED:")
        print("=" * 50)
        print("1. ❌ Django server may not be running")
        print("2. 🔧 Check: python manage.py runserver")
        print("3. 🌐 Verify server is accessible at", host)
        print("4. 📋 Check Django logs for errors")
        print("\\n⛔ Fix server issues before running load tests!")
        
        return 1

if __name__ == "__main__":
    exit(main())