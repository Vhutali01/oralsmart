# Quick Start Guide for Load Testing

## Prerequisites Setup

Before running load tests, ensure your environment is properly configured:

### 1. Install Dependencies

```bash
# If using virtual environment (recommended)
python -m venv venv
venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On Linux/Mac

# Install Django and requirements
pip install -r src/requirements.txt
pip install locust matplotlib seaborn pandas numpy beautifulsoup4 faker requests
```

### 2. Database Setup

```bash
cd src
python manage.py migrate
python manage.py collectstatic --noinput
```

### 3. Create Test User (Optional)

```bash
python manage.py createsuperuser
# or create regular user for testing
```

## Starting the Load Testing

### Step 1: Start Django Server

**Terminal 1:**
```bash
cd src
python manage.py runserver
```

Keep this terminal open during testing.

### Step 2: Test Server Connectivity  

**Terminal 2:**
```bash
python loadtesting/test_server_connectivity.py
```

You should see output like:
```
✅ Server is running and all endpoints are accessible!
🎯 Ready for load testing!
```

### Step 3: Run Load Tests

Choose one of these options:

**Option A: Interactive Menu**
```bash
python loadtesting/run_virtual_user_tests.py
```

**Option B: Command Line**
```bash
# Small test first
python loadtesting/virtual_user_load_test.py --scenario "Patient browsing and search" --users 50

# Full test
python loadtesting/virtual_user_load_test.py --scenario "Patient management workflow" --users 500
```

**Option C: Windows Batch**
```bash
loadtesting\run_virtual_user_tests.bat
```

## Common Setup Issues

### Issue: "No module named 'django'"
**Solution:**
```bash
pip install django
# or
pip install -r src/requirements.txt
```

### Issue: "Connection refused"
**Solution:**
1. Make sure Django server is running: `python manage.py runserver`
2. Check server is accessible: http://localhost:8000
3. Test connectivity: `python loadtesting/test_server_connectivity.py`

### Issue: Database errors
**Solution:**
```bash
cd src
python manage.py migrate
```

### Issue: Static files missing
**Solution:**
```bash
cd src
python manage.py collectstatic --noinput
```

## Recommended Testing Sequence

1. **Start Small**: Begin with 10-50 users
2. **Test Connectivity**: Always run connectivity test first
3. **Monitor Server**: Watch Django terminal for errors
4. **Scale Gradually**: Increase users as system proves stable
5. **Analyze Results**: Review generated reports and graphs

## Expected Results Location

Reports are saved to:
```
loadtesting/reports/virtual_users_{timestamp}/
├── Load_Time_Report_500_users_Patient_management_workflow.png
├── Latency_Report_500_users_Patient_management_workflow.png
├── Connect_Time_Report_500_users_Patient_management_workflow.png
└── Summary_Report_500_users_Patient_management_workflow.md
```

## Performance Baselines

**Good Performance:**
- Load Time: < 200ms
- Latency (P95): < 500ms  
- Failure Rate: < 1%

**Acceptable Performance:**
- Load Time: < 500ms
- Latency (P95): < 1000ms
- Failure Rate: < 5%

## Support

If you encounter issues:

1. Check Django server logs in Terminal 1
2. Run connectivity test: `python loadtesting/test_server_connectivity.py`
3. Start with small user counts (10-50 users)
4. Review the error reports in this guide