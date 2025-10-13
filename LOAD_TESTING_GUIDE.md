# 🔥 OralSmart Load Testing Guide

This guide provides comprehensive instructions for load testing the OralSmart Django application using Locust.

## 📋 Table of Contents

1. [Setup](#setup)
2. [Test Scenarios](#test-scenarios) 
3. [Running Tests](#running-tests)
4. [Interpreting Results](#interpreting-results)
5. [Performance Targets](#performance-targets)
6. [Troubleshooting](#troubleshooting)

## 🚀 Setup

### 1. Install Dependencies

```powershell
# Install load testing dependencies
pip install -r requirements-loadtest.txt
```

### 2. Setup Test Data

```powershell
# Navigate to project root
cd C:\Users\vhuta\dev\oralsmart

# Create test users and patients
python loadtesting\setup_test_data.py
```

This creates:
- 5 test users (password: `loadtest123`)
- 100 test patients
- Assessment data for ~60% of patients

### 3. Prepare Your Django Application

Ensure your Django app is running:

```powershell
# Navigate to src directory
cd src

# Start Django development server
python manage.py runserver
```

## 🎯 Test Scenarios

### User Types

| User Type | Weight | Behavior | Purpose |
|-----------|--------|----------|---------|
| **OralSmartUser** | 50% | Complete workflows (create patients, assessments, reports) | Normal usage patterns |
| **ReadOnlyUser** | 40% | Browse data, view reports | Read-heavy workloads |
| **HeavyUser** | 10% | Resource-intensive operations (ML, PDF generation) | Stress testing |

### Key Workflows Tested

1. **Authentication Flow**
   - Landing page access
   - User login/logout
   - Session management

2. **Patient Management**
   - Create new patients
   - Browse patient lists
   - Search and pagination
   
3. **Assessment Workflows**
   - Dental screening forms
   - Dietary screening forms
   - Form validation and submission

4. **Report Generation** 
   - PDF report creation
   - ML risk predictions
   - Email report sending

5. **System Navigation**
   - Clinic browsing
   - Profile management
   - Multi-page workflows

## 🔥 Running Tests

### Quick Start (Recommended)

```powershell
# Navigate to project root
cd C:\Users\vhuta\dev\oralsmart

# Run basic load test (10 users, 5 minutes)
locust -f loadtesting\locustfile.py --host=http://localhost:8000 --users=10 --spawn-rate=2 --run-time=5m --html=loadtesting\reports\load_test_report.html
```

### Web UI Mode (Interactive)

```powershell
# Start Locust web interface
locust -f loadtesting\locustfile.py --host=http://localhost:8000

# Open browser and go to: http://localhost:8089
# Configure test parameters in the web UI
```

### Advanced Test Scenarios

#### Light Load Test
```powershell
# Simulate 5 concurrent users for 3 minutes
locust -f loadtesting\locustfile.py --host=http://localhost:8000 --users=5 --spawn-rate=1 --run-time=3m --html=loadtesting\reports\light_load_report.html
```

#### Moderate Load Test  
```powershell
# Simulate 25 concurrent users for 10 minutes
locust -f loadtesting\locustfile.py --host=http://localhost:8000 --users=25 --spawn-rate=3 --run-time=10m --html=loadtesting\reports\moderate_load_report.html --csv=loadtesting\reports\moderate_stats
```

#### Stress Test
```powershell
# Simulate 50+ concurrent users to find breaking point
locust -f loadtesting\locustfile.py --host=http://localhost:8000 --users=50 --spawn-rate=5 --run-time=15m --html=loadtesting\reports\stress_test_report.html --csv=loadtesting\reports\stress_stats
```

#### Spike Test
```powershell
# Rapid user increase to test system resilience
locust -f loadtesting\locustfile.py --host=http://localhost:8000 --users=30 --spawn-rate=10 --run-time=5m --html=loadtesting\reports\spike_test_report.html
```

### Configuration File Usage

You can use the provided configuration file:

```powershell
locust -f loadtesting\locustfile.py --config=loadtesting\locust.conf
```

## 📊 Interpreting Results

### Key Metrics to Monitor

#### Response Times
- **Average Response Time**: Should be < 2 seconds for most requests
- **95th Percentile**: Should be < 5 seconds
- **99th Percentile**: Should be < 10 seconds

#### Throughput
- **Requests per Second (RPS)**: Higher is better
- **Users**: Maximum concurrent users without degradation

#### Error Rates
- **Failure Rate**: Should be < 1% under normal load
- **Error Types**: Check for specific error patterns

### Reading the HTML Report

The HTML report includes:

1. **Statistics Table**
   - Request counts and response times
   - Error rates by endpoint
   - Request distribution

2. **Charts**
   - Response time over time
   - Users over time  
   - Requests per second

3. **Failures**
   - Detailed error information
   - Failure distribution

### Performance Indicators

#### ✅ Good Performance
- Average response time < 2s
- 95th percentile < 5s
- Error rate < 1%
- Stable performance over time

#### ⚠️ Warning Signs
- Average response time 2-5s
- 95th percentile 5-10s
- Error rate 1-5%
- Gradual performance degradation

#### 🚨 Performance Issues
- Average response time > 5s
- 95th percentile > 10s
- Error rate > 5%
- Memory leaks or crashes

## 🎯 Performance Targets

### Baseline Targets (Development)

| Metric | Target | Acceptable | Poor |
|--------|--------|------------|------|
| Response Time (avg) | < 1s | < 2s | > 5s |
| Response Time (95th) | < 3s | < 5s | > 10s |
| Error Rate | < 0.5% | < 1% | > 2% |
| Concurrent Users | 20+ | 10+ | < 5 |

### Production Targets

| Metric | Target | Acceptable | Poor |
|--------|--------|------------|------|
| Response Time (avg) | < 500ms | < 1s | > 3s |
| Response Time (95th) | < 2s | < 3s | > 5s |
| Error Rate | < 0.1% | < 0.5% | > 1% |
| Concurrent Users | 100+ | 50+ | < 20 |

### Resource-Intensive Operations

Special targets for heavy operations:

| Operation | Target Response Time | Acceptable | Poor |
|-----------|---------------------|------------|------|
| PDF Generation | < 3s | < 5s | > 10s |
| ML Prediction | < 2s | < 3s | > 5s |
| Report Email | < 5s | < 10s | > 15s |
| Large Search | < 1s | < 2s | > 5s |

## 🔧 Troubleshooting

### Common Issues

#### High Response Times
**Possible Causes:**
- Database query inefficiency
- Unoptimized views
- Static file serving issues
- ML model loading delays

**Solutions:**
- Enable Django Debug Toolbar
- Optimize database queries
- Implement caching
- Use async processing for heavy tasks

#### High Error Rates
**Possible Causes:**
- CSRF token issues
- Database connection limits
- Memory exhaustion
- Unhandled exceptions

**Solutions:**
- Check Django logs
- Monitor database connections
- Increase memory allocation
- Implement proper error handling

#### Memory Issues
**Possible Causes:**
- Django not releasing memory
- Large file processing
- ML model memory usage
- Database connection leaks

**Solutions:**
- Monitor memory usage
- Implement pagination
- Use streaming responses
- Clean up resources properly

### Django-Specific Considerations

#### CSRF Protection
The load tests handle Django CSRF tokens automatically. If you see CSRF errors:
- Check token extraction logic
- Ensure proper session handling
- Verify middleware configuration

#### Database Performance
Monitor your database during load tests:
- Connection pool usage
- Query execution time
- Lock contention
- Index usage

#### Static Files
For production testing:
- Use proper static file serving (nginx)
- Enable compression
- Implement CDN if needed

### Performance Optimization Tips

#### Database
```python
# In your Django settings
DATABASES = {
    'default': {
        # ... your database config
        'CONN_MAX_AGE': 60,  # Connection pooling
        'OPTIONS': {
            'MAX_CONNS': 20,  # Max connections
        }
    }
}
```

#### Caching
```python
# Enable caching for better performance
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

#### Session Storage
```python
# Use database sessions for load testing
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 3600  # 1 hour
```

## 📈 Best Practices

### Before Load Testing
1. **Test in isolated environment** - Use separate database
2. **Monitor resources** - CPU, memory, disk, network
3. **Baseline measurement** - Test single user first
4. **Clean test data** - Use consistent, realistic data

### During Load Testing
1. **Monitor system resources** - Use Task Manager/htop
2. **Check application logs** - Monitor for errors
3. **Watch database performance** - Query times and connections
4. **Document observations** - Note any anomalies

### After Load Testing
1. **Analyze results thoroughly** - Don't just look at averages
2. **Compare with baselines** - Track performance over time
3. **Document findings** - Create actionable reports
4. **Plan optimizations** - Prioritize performance improvements

### Continuous Testing
1. **Automate tests** - Run load tests in CI/CD
2. **Set up monitoring** - Track production performance
3. **Regular testing** - Test with each major release
4. **Performance budgets** - Set and enforce performance limits

## 🔍 Advanced Analysis

### Custom Metrics
You can add custom metrics to track specific OralSmart features:

```python
# Example: Track ML prediction success rate
@task
def test_ml_prediction_success(self):
    with self.client.post('/ml/predict-risk/', catch_response=True) as response:
        if 'risk_level' in response.text:
            response.success()
        else:
            response.failure("ML prediction failed")
```

### Database Analysis
Monitor these database metrics during load testing:
- Connection count
- Query execution time
- Lock wait time
- Buffer pool usage (MySQL/PostgreSQL)

### Application-Specific Monitoring
For OralSmart, pay special attention to:
- PDF generation times
- ML model response times
- File upload performance
- Email sending delays

## 🎯 Conclusion

Load testing is crucial for ensuring OralSmart can handle real-world usage patterns. Use this guide to:

1. **Establish baselines** - Know your current performance
2. **Identify bottlenecks** - Find and fix performance issues
3. **Plan capacity** - Understand scaling requirements
4. **Monitor trends** - Track performance over time

Remember: **Load testing is not a one-time activity**. Regular testing helps maintain optimal performance as your application grows.

---

For questions or issues with load testing, check the Django logs and Locust documentation, or consult the development team.