# Virtual User Load Testing Guide

## Overview

This guide covers the **Virtual User Load Testing System** for OralSmart - a professional load testing solution that generates industry-standard performance reports with specific virtual user scenarios.

## Key Features

- **Specific Virtual User Scenarios**: Test with exact user counts (500, 1000, etc.)
- **Professional Reports**: Generate "Load time report with X virtual users: Y test scenario" 
- **3 Iterations per Test**: Statistical accuracy through multiple test runs
- **Multiple Report Types**: Load Time, Latency, and Connect Time reports
- **Graphical Visualization**: Response time analysis with professional charts

## Quick Start

### 1. Prerequisites

Ensure you have the required dependencies installed:

```bash
pip install locust matplotlib seaborn pandas numpy beautifulsoup4 faker
```

### 2. Start Django Server

```bash
cd src
python manage.py runserver
```

### 3. Run Load Tests

**Option A: Menu-Driven Interface**
```bash
python loadtesting/run_virtual_user_tests.py
```

**Option B: Command Line**
```bash
python loadtesting/virtual_user_load_test.py --scenario "Preview asset test" --users 500
```

**Option C: Windows Batch File**
```bash
loadtesting/run_virtual_user_tests.bat
```

## Test Scenarios

### Healthcare-Specific Scenarios

1. **Patient management workflow**
   - Tests patient creation, editing, and browsing
   - Simulates healthcare staff managing patient records
   - Includes patient search and pagination functionality
   - Users: 500 or 1000

2. **Assessment screening workflow**
   - Tests dental and dietary screening assessments
   - Simulates comprehensive patient evaluations
   - Includes form submissions with detailed medical data
   - Users: 500 or 1000

3. **Report generation stress test**
   - Tests PDF report generation and data export
   - Simulates high-volume report creation scenarios
   - Includes clinic summaries and statistical reports
   - Users: 500 or 1000

4. **ML prediction performance test**
   - Tests machine learning risk prediction APIs
   - Simulates batch predictions and model performance checks
   - Includes complex algorithmic computations
   - Users: 500 or 1000

5. **Patient browsing and search**
   - Tests read-only patient data access
   - Simulates staff browsing patient records
   - Includes search functionality and pagination
   - Users: 500 or 1000

6. **Clinic directory browsing**
   - Tests clinic information browsing
   - Simulates users searching for healthcare facilities
   - Includes filtering and search capabilities
   - Users: 500 or 1000

7. **Authentication load test**
   - Tests login/logout cycles under load
   - Simulates concurrent user authentication
   - Includes failed login attempt handling
   - Users: 500 or 1000

8. **Mixed healthcare workflow**
   - Tests complete patient visit workflows
   - Simulates realistic healthcare scenarios
   - Combines patient management, assessments, and reporting
   - Users: 500 or 1000

### Custom Scenarios

You can define custom scenarios with any name and user count:

```bash
python loadtesting/virtual_user_load_test.py --scenario "Emergency department load test" --users 750
```

## Scenario Details

### What Each Scenario Actually Tests

#### 1. Patient Management Workflow
**Locust User Class**: `PatientManagementUser`
**Endpoints Tested**:
- `/create_patient/` - Patient creation forms
- `/patient_list/` - Patient listing and pagination  
- `/patient/{id}/` - Individual patient records
- `/edit_patient/{id}/` - Patient record updates

**Simulated Actions**:
- Creating new patient records with realistic data
- Browsing paginated patient lists
- Searching patients by name/criteria
- Updating existing patient information

#### 2. Assessment Screening Workflow  
**Locust User Class**: `AssessmentWorkflowUser`
**Endpoints Tested**:
- `/assessments/dental_screening/{id}/` - Dental health assessments
- `/assessments/dietary_screening/{id}/` - Dietary assessments
- `/assessments/history/{id}/` - Assessment history
- `/assessments/view/{id}/` - Assessment details

**Simulated Actions**:
- Completing comprehensive dental examinations
- Recording dietary screening information
- Reviewing previous assessment history
- Submitting complex form data with validation

#### 3. Report Generation Stress Test
**Locust User Class**: `ReportGenerationUser` 
**Endpoints Tested**:
- `/reports/report/{id}/` - Report viewing pages
- `/reports/{id}/` - PDF report generation
- `/reports/clinic_summary/` - Clinic-wide reports
- `/reports/export/patients/` - Data export functions

**Simulated Actions**:
- Generating PDF reports (CPU/memory intensive)
- Creating summary and statistical reports
- Exporting patient and assessment data
- Testing report rendering under load

#### 4. ML Prediction Performance Test
**Locust User Class**: `MLPredictionUser`
**Endpoints Tested**:
- `/ml/predict-risk/` - Individual risk predictions
- `/ml/batch-predict/` - Batch prediction processing
- `/ml/model-status/` - Model health checks
- `/ml/model-metrics/` - Performance metrics

**Simulated Actions**:
- Single patient risk calculations
- Batch processing multiple predictions
- Model performance monitoring
- Complex algorithmic computations

#### 5. Patient Browsing and Search
**Locust User Class**: `ReadOnlyUser`
**Endpoints Tested**:
- `/patient_list/` - Patient browsing
- `/reports/report/{id}/` - Report viewing
- `/clinics/` - Clinic directory
- Search and pagination endpoints

**Simulated Actions**:
- Read-only patient data access
- Report viewing without generation
- Search functionality testing
- High-frequency browsing patterns

#### 6. Clinic Directory Browsing
**Locust User Class**: `ReadOnlyUser` (clinic-focused tasks)
**Endpoints Tested**:
- `/clinics/` - Clinic listings
- `/clinics/?search=` - Clinic search
- Clinic detail pages

**Simulated Actions**:
- Browsing healthcare facility directories
- Searching clinics by specialty/location
- Viewing clinic information and details

#### 7. Authentication Load Test
**Locust User Class**: `AuthenticationLoadUser`
**Endpoints Tested**:
- `/login_user/` - User authentication
- `/logout/` - Session termination
- Session management endpoints

**Simulated Actions**:
- Rapid login/logout cycles
- Concurrent session handling
- Failed authentication attempts
- Session security testing

#### 8. Mixed Healthcare Workflow
**Locust User Class**: `MixedHealthcareUser`
**Endpoints Tested**: All major endpoints in sequence
**Simulated Actions**:
- Complete patient visit workflows
- End-to-end healthcare scenarios
- Combined patient management, assessments, and reporting
- Realistic healthcare professional usage patterns

## Generated Reports

Each test run generates multiple professional reports:

### 1. Load Time Report
- **Format**: `Load_Time_Report_{users}_users_{scenario}.png`
- **Content**: Bar chart showing load times for each iteration
- **Y-axis**: Load Time (ms)
- **X-axis**: Iteration number (1, 2, 3)

### 2. Latency Report
- **Format**: `Latency_Report_{users}_users_{scenario}.png`
- **Content**: Line chart showing 95th percentile latency
- **Y-axis**: Latency (ms)
- **X-axis**: Iteration number (1, 2, 3)

### 3. Connect Time Report
- **Format**: `Connect_Time_Report_{users}_users_{scenario}.png`
- **Content**: Scatter plot with trend line for connection times
- **Y-axis**: Connect Time (ms)
- **X-axis**: Iteration number (1, 2, 3)

### 4. Summary Report
- **Format**: `Summary_Report_{users}_users_{scenario}.md`
- **Content**: Comprehensive markdown report with all metrics

## Report Location

All reports are saved to:
```
loadtesting/reports/virtual_users_{timestamp}/
```

Example:
```
loadtesting/reports/virtual_users_20241211_143022/
├── Load_Time_Report_500_users_Preview_asset_test.png
├── Latency_Report_500_users_Preview_asset_test.png
├── Connect_Time_Report_500_users_Preview_asset_test.png
├── Summary_Report_500_users_Preview_asset_test.md
└── [Raw Locust CSV/HTML files...]
```

## Command Line Usage

### Basic Syntax
```bash
python loadtesting/virtual_user_load_test.py [OPTIONS]
```

### Required Parameters
- `--scenario`: Test scenario name (e.g., "Preview asset test")
- `--users`: Number of virtual users (e.g., 500, 1000)

### Optional Parameters
- `--host`: Target host (default: http://localhost:8000)

### Examples

```bash
# Healthcare workflow scenarios
python loadtesting/virtual_user_load_test.py --scenario "Patient management workflow" --users 500
python loadtesting/virtual_user_load_test.py --scenario "Assessment screening workflow" --users 1000

# Performance testing scenarios
python loadtesting/virtual_user_load_test.py --scenario "Report generation stress test" --users 500
python loadtesting/virtual_user_load_test.py --scenario "ML prediction performance test" --users 1000

# User experience scenarios
python loadtesting/virtual_user_load_test.py --scenario "Patient browsing and search" --users 750
python loadtesting/virtual_user_load_test.py --scenario "Authentication load test" --users 500

# Comprehensive scenarios
python loadtesting/virtual_user_load_test.py --scenario "Mixed healthcare workflow" --users 1000

# Custom scenario
python loadtesting/virtual_user_load_test.py --scenario "Emergency department load test" --users 250

# Different host
python loadtesting/virtual_user_load_test.py --scenario "Patient management workflow" --users 500 --host "https://your-server.com"
```

## Understanding the Results

### Load Time
- **Definition**: Average response time for all requests
- **Good**: < 200ms
- **Acceptable**: 200-500ms
- **Poor**: > 500ms

### Latency (95th Percentile)
- **Definition**: 95% of requests complete within this time
- **Good**: < 500ms
- **Acceptable**: 500-1000ms
- **Poor**: > 1000ms

### Connect Time
- **Definition**: Time to establish connection to server
- **Good**: < 50ms
- **Acceptable**: 50-100ms
- **Poor**: > 100ms

### Requests Per Second (RPS)
- **Definition**: Number of requests handled per second
- **Higher is better**: Indicates server throughput

### Failure Rate
- **Definition**: Percentage of failed requests
- **Good**: < 1%
- **Acceptable**: 1-5%
- **Poor**: > 5%

## Test Configuration

### Default Settings
- **Test Duration**: 2 minutes per iteration
- **Spawn Rate**: Gradually ramp up users (min(50, users/10) per second)
- **Iterations**: 3 iterations per test scenario
- **Timeout**: 5 minutes maximum per iteration

### Customizing Settings

To modify test parameters, edit `virtual_user_load_test.py`:

```python
# Change test duration
test_duration = "3m"  # 3 minutes instead of 2

# Change spawn rate
spawn_rate = 100  # 100 users per second

# Change timeout
timeout = 600  # 10 minutes
```

## Troubleshooting

### Server Connectivity Issues

If you see `ConnectionRefusedError` errors:

1. **Check Django Server Status**
   ```bash
   # Test server connectivity
   python loadtesting/test_server_connectivity.py
   ```

2. **Start Django Server**
   ```bash
   # Option A: Use the setup script
   loadtesting/start_server.bat
   
   # Option B: Manual start
   cd src
   python manage.py runserver
   ```

3. **Verify Server is Running**
   - Open browser to http://localhost:8000
   - Should see OralSmart landing page
   - Check terminal for Django startup messages

### Common Issues and Solutions

1. **"Connection refused" Error**
   ```
   Solution: Ensure Django server is running on http://localhost:8000
   Check: python loadtesting/test_server_connectivity.py
   ```

2. **404 Not Found Errors**
   ```
   These are partially normal for:
   - /patient/XX/ (patients may not exist)
   - /assessments/history/XX/ (assessments may not exist)
   
   High 404 rates indicate endpoint mismatch - check that load test
   scenarios match your actual Django URL patterns.
   ```

3. **"No module named 'locust'" Error**
   ```
   Solution: pip install locust matplotlib seaborn pandas numpy beautifulsoup4 faker
   ```

4. **Tests Taking Too Long**
   ```
   Solution: Reduce test duration or user count for initial testing
   Edit virtual_user_load_test.py: test_duration = "1m"
   ```

5. **High Failure Rates**
   ```
   Solution: 
   - Check Django server logs for errors
   - Reduce spawn rate: spawn_rate = 10 (in virtual_user_load_test.py)
   - Ensure adequate server resources
   - Check database connectivity
   ```

6. **Authentication Failures**
   ```
   Solution:
   - Ensure test users exist in Django database
   - Check Django login URLs match load test expectations
   - Verify CSRF token handling is working
   ```

### Debug Mode

For detailed debugging information:

```bash
# Test server connectivity first
python loadtesting/test_server_connectivity.py

# Run small test to identify issues
python loadtesting/virtual_user_load_test.py --scenario "Patient browsing and search" --users 10

# Check Django server logs in the terminal where you ran manage.py runserver
```

### Expected Error Patterns

Some errors are normal in load testing:

- **Patient/Assessment 404s**: Normal when testing with random IDs
- **Authentication Redirects**: Normal for protected endpoints
- **Occasional Connection Issues**: Normal under high load

**Concerning Error Patterns:**
- High rate of connection refused errors
- All requests failing
- Django server crashes
- Database connection errors

## Performance Optimization Tips

### Server Side
1. **Database Optimization**: Ensure proper indexing
2. **Caching**: Implement Redis/Memcached
3. **Static Files**: Use CDN for static assets
4. **Connection Pooling**: Configure database connection pools

### Test Side
1. **Gradual Ramp-up**: Start with lower user counts
2. **Monitor Resources**: Watch CPU/Memory on test machine
3. **Network Bandwidth**: Ensure adequate network capacity
4. **Distributed Testing**: Use multiple test machines for high loads

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Load Testing
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install locust matplotlib seaborn pandas numpy
      
      - name: Start Django server
        run: |
          cd src
          python manage.py migrate
          python manage.py runserver &
          sleep 10
      
      - name: Run load tests
        run: |
          python loadtesting/virtual_user_load_test.py --scenario "CI Pipeline test" --users 100
      
      - name: Upload reports
        uses: actions/upload-artifact@v3
        with:
          name: load-test-reports
          path: loadtesting/reports/
```

## Best Practices

1. **Start Small**: Begin with 50-100 users, then scale up
2. **Baseline Testing**: Establish performance baselines
3. **Regular Testing**: Run tests after major changes
4. **Multiple Scenarios**: Test different user workflows
5. **Monitor Trends**: Track performance over time
6. **Resource Monitoring**: Watch server resources during tests
7. **Realistic Data**: Use production-like test data
8. **Test Environment**: Mirror production configuration

## Support

For issues or questions:

1. Check the generated HTML reports for detailed error information
2. Review Django server logs for backend issues
3. Monitor system resources during testing
4. Ensure all dependencies are properly installed

## Advanced Usage

### Custom User Behaviors

To add new user behaviors, edit `loadtesting/locustfile.py`:

```python
class CustomUser(DjangoUserMixin, HttpUser):
    wait_time = between(1, 3)
    
    @task
    def custom_workflow(self):
        # Your custom test logic here
        pass
```

### Multiple Host Testing

Test against multiple environments:

```bash
# Development
python loadtesting/virtual_user_load_test.py --scenario "Preview asset test" --users 100 --host "http://localhost:8000"

# Staging
python loadtesting/virtual_user_load_test.py --scenario "Preview asset test" --users 500 --host "https://staging.oralsmart.com"

# Production (with caution!)
python loadtesting/virtual_user_load_test.py --scenario "Preview asset test" --users 50 --host "https://oralsmart.com"
```

This completes the Virtual User Load Testing system - providing professional, industry-standard load testing reports with the specific scenarios and user counts you requested.