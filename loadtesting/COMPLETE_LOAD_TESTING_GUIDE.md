# 🚀 OralSmart Load Testing - Complete Guide

**The definitive guide for load testing the OralSmart healthcare application**

---

## 📋 Table of Contents

1. [Quick Start](#-quick-start)
2. [Test Runners Overview](#-test-runners-overview)
3. [Setup & Prerequisites](#-setup--prerequisites)
4. [Running Different Test Types](#-running-different-test-types)
5. [Understanding Results](#-understanding-results)
6. [Performance Thresholds](#-performance-thresholds)
7. [Troubleshooting](#-troubleshooting)

---

## 🎯 Quick Start

**Want to run a quick test? Here are the essential commands:**

```bash
# 1. Start Django server
cd src && python manage.py runserver

# 2. Quick scaling test (recommended)
python loadtesting/virtual_user_load_test.py --scenario "Patient Management" --user-range "5,10,15,20,25"

# 3. Single high-load test
python loadtesting/virtual_user_load_test.py --scenario "Healthcare Workflow" --users 100

# 4. Multi-pattern comparison
python loadtesting/enhanced_load_test.py --scenarios light_load moderate_load

# 5. Menu-driven interface
python loadtesting/run_virtual_user_tests.py
```

---

## 🔧 Test Runners Overview

OralSmart has **3 test runners** - here's when to use each:

### 1. **`locustfile.py`** - Core Test Definitions
**What it is**: The foundation - contains all user behaviors and scenarios
**Use when**: Running manual Locust tests or need custom control
```bash
locust -f loadtesting/locustfile.py --host http://localhost:8000 --users 50 --spawn-rate 2 --run-time 3m
```

### 2. **`virtual_user_load_test.py`** - Production Test Runner ⭐ **RECOMMENDED**
**What it is**: Advanced orchestrator with professional reporting and scaling analysis
**Use when**: 
- Production performance validation
- Scaling analysis (response time vs users)
- Professional reports for stakeholders
- Statistical accuracy (3 iterations per test)

```bash
# Single user count with detailed reports
python loadtesting/virtual_user_load_test.py --scenario "Patient Management" --users 500

# Scaling analysis across multiple user counts
python loadtesting/virtual_user_load_test.py --scenario "Assessment Workflow" --user-range "10-50-10"
```

### 3. **`enhanced_load_test.py`** - Multi-Scenario Runner
**What it is**: Runs predefined scenarios (light/moderate/heavy load) with comparative analysis
**Use when**: Want to compare different load patterns quickly
```bash
python loadtesting/enhanced_load_test.py --scenarios light_load moderate_load --iterations 3
```

---

## 🛠️ Setup & Prerequisites

### 1. Install Dependencies
```bash
pip install -r requirements-loadtest.txt
```

**Core dependencies installed:**
- `locust` - Load testing framework
- `matplotlib`, `seaborn` - Graph generation
- `pandas`, `numpy` - Data analysis
- `beautifulsoup4` - HTML parsing
- `faker` - Test data generation

### 2. Setup Test Data
```bash
python loadtesting/setup_test_data.py
```

**Creates:**
- 5 test users (username: `testuser1-5`, password: `testpass123`)
- 100 test patients with realistic data
- Assessment data for ~60% of patients

### 3. Start Django Server
```bash
cd src
python manage.py runserver
```

**Verify server**: Visit http://localhost:8000 and login with test credentials

---

## 🎮 Running Different Test Types

### **Scenario 1: Quick Performance Check**
Test if your app handles basic load:
```bash
python loadtesting/virtual_user_load_test.py --scenario "Quick Check" --users 10
```
**Output**: Load time, latency, and connect time reports with 3 iterations

### **Scenario 2: Scaling Analysis** ⭐ **MOST USEFUL**
See how performance degrades as users increase:
```bash
python loadtesting/virtual_user_load_test.py --scenario "Patient Management" --user-range "5,10,15,20,25,30"
```
**Output**: Response time vs users plots showing performance scaling

### **Scenario 3: High-Load Stress Test**
Test production-scale load:
```bash
python loadtesting/virtual_user_load_test.py --scenario "Production Load" --users 500
```
**Output**: Professional reports suitable for stakeholder review

### **Scenario 4: Multi-Pattern Comparison** 
Compare light vs moderate vs heavy load patterns:
```bash
python loadtesting/enhanced_load_test.py --scenarios light_load moderate_load heavy_load
```
**Output**: Comparative analysis across predefined load patterns

### **Enhanced Load Testing - Detailed Usage**

The `enhanced_load_test.py` runner provides **predefined scenarios** with **comparative analysis**:

#### **Available Scenarios:**
- **`quick_test`**: 1,3,5 users for 30 seconds (rapid feedback)
- **`light_load`**: 1,3,5,8,10 users for 3 minutes (normal daily usage)
- **`moderate_load`**: 10,15,20,25,30 users for 3 minutes (peak usage periods)  
- **`heavy_load`**: 20,30,40,50,60 users for 4 minutes (stress testing)

#### **Enhanced Testing Commands:**
```bash
# Run all scenarios with default settings (3 iterations each)
python loadtesting/enhanced_load_test.py

# Run specific scenarios only
python loadtesting/enhanced_load_test.py --scenarios light_load moderate_load

# Increase statistical accuracy
python loadtesting/enhanced_load_test.py --iterations 5

# Test different target server
python loadtesting/enhanced_load_test.py --host http://staging.oralsmart.com

# Check server connectivity before testing
python loadtesting/enhanced_load_test.py --check-server

# Quick validation test (fastest option)
python loadtesting/enhanced_load_test.py --scenarios quick_test --iterations 1

# Comprehensive pre-production validation
python loadtesting/enhanced_load_test.py --scenarios light_load moderate_load heavy_load --iterations 5
```

#### **Enhanced Output Structure:**
```
reports/test_run_20251022_143022/
├── 📊 light_load_performance_graphs.png        # 4-panel overview
├── 📈 light_load_detailed_response_times.png   # Individual iterations
├── 📊 moderate_load_performance_graphs.png     
├── 📈 moderate_load_detailed_response_times.png
├── 📊 heavy_load_performance_graphs.png        
├── 📈 heavy_load_detailed_response_times.png   
├── 🔄 scenarios_comparison.png                 # Cross-scenario comparison
├── 📋 load_test_summary.md                     # Comprehensive text report
└── 📁 *.csv, *.html                           # Raw Locust data
```

#### **Enhanced Load Test Use Cases:**

**🔍 Development Testing:**
```bash
# Quick smoke test during development (< 2 minutes)
python loadtesting/enhanced_load_test.py --scenarios quick_test --iterations 1
```

**📊 Performance Baseline:**
```bash
# Establish performance baseline across all load patterns (~20 minutes)
python loadtesting/enhanced_load_test.py --iterations 3
```

**🚀 Pre-Production Validation:**
```bash
# Comprehensive validation before deployment (~30 minutes)
python loadtesting/enhanced_load_test.py --scenarios light_load moderate_load heavy_load --iterations 5
```

**🔄 Regression Testing:**
```bash
# Compare performance after code changes
python loadtesting/enhanced_load_test.py --scenarios moderate_load --host http://staging.oralsmart.com
```

**📈 Capacity Planning:**
```bash
# Understand load characteristics for infrastructure planning
python loadtesting/enhanced_load_test.py --scenarios heavy_load --iterations 5
```

#### **Enhanced vs Virtual User Testing - When to Use Which:**

| Use Enhanced Load Test When | Use Virtual User Load Test When |
|----------------------------|--------------------------------|
| 🔄 Comparing multiple load patterns | 📊 Deep analysis of specific scenarios |
| ⚡ Quick development feedback | 🎯 Production validation with exact user counts |
| 📊 Establishing performance baselines | 📈 Scaling analysis (response time vs users) |
| 🚀 Pre-deployment validation | 📋 Professional stakeholder reports |
| 🔍 Finding optimal load characteristics | 🔢 Testing specific user counts (500, 1000+) |

### **Advanced User Range Formats**
```bash
# Comma-separated specific counts
--user-range "1,5,10,15,20"

# Range with step: start-end-step (5 to 50 users, increment by 5)
--user-range "5-50-5"

# The test that created virtual_users_20251020_175842 folder:
python loadtesting/virtual_user_load_test.py --scenario "Patient management workflow" --user-range "0-150-5"
```

---

## 📊 Understanding Results

### **Output Directory Structure**

#### **Virtual User Load Test Output:**
```
reports/virtual_users_20251021_143052/
├── 📈 Load_Time_Report_100_users_Patient_Management.png
├── 📉 Latency_Report_100_users_Patient_Management.png  
├── 🔗 Connect_Time_Report_100_users_Patient_Management.png
├── 📊 Scaling_Analysis_Patient_Management.png
├── 📈 ResponseTime_vs_Users_Patient_Management.png
├── 📋 Summary_Report_100_users_Patient_Management.md
└── 📁 Raw CSV/HTML files from Locust
```

#### **Enhanced Load Test Output:**
```
reports/test_run_20251022_143022/
├── 📊 light_load_performance_graphs.png        # 4-panel performance overview
├── 📈 light_load_detailed_response_times.png   # Individual iteration tracking
├── 📊 moderate_load_performance_graphs.png     
├── 📈 moderate_load_detailed_response_times.png
├── 📊 heavy_load_performance_graphs.png        
├── 📈 heavy_load_detailed_response_times.png   
├── 🔄 scenarios_comparison.png                 # Cross-scenario comparison
├── 📋 load_test_summary.md                     # Comprehensive text report
└── 📁 *.csv, *.html                           # Raw Locust reports
```

### **Key Report Types**

#### **1. Enhanced Load Test Graphs**

**Performance Overview Graphs** (`*_performance_graphs.png`):
- 📊 **Average Response Time vs Users** - How response time scales with user load
- 📈 **95th Percentile Response Time vs Users** - P95 response times (worst-case scenarios)
- 🚀 **Requests per Second vs Users** - Throughput scaling characteristics
- ❌ **Failure Rate vs Users** - Error rates under different load conditions

**Detailed Response Time Graphs** (`*_detailed_response_times.png`):
- Individual lines for each iteration (shows consistency)
- Bold average line across all iterations
- Statistical annotations for key performance points
- Error bars showing variability between runs

**Scenario Comparison Graph** (`scenarios_comparison.png`):
- Response time comparison across all tested scenarios
- Shows which scenarios perform better under load
- Useful for understanding system behavior patterns

#### **2. Virtual User Load Test Reports** 

**Load Time Report** 📈:
- **Shows**: Average response time for each iteration
- **Format**: Bar chart with statistical annotations
- **Use**: Verify consistency across test runs

**Latency Report** 📉:
- **Shows**: 95th percentile response times
- **Format**: Line graph with trend analysis
- **Use**: Identify worst-case user experience

**Connect Time Report** 🔗:
- **Shows**: Connection establishment times
- **Format**: Scatter plot with trend line
- **Use**: Network and server startup performance

**Scaling Analysis** 📊 ⭐ **MOST IMPORTANT**:
- **Shows**: 4-panel view of performance vs user count
  - Average Response Time vs Users
  - 95th Percentile Latency vs Users  
  - Throughput (RPS) vs Users
  - Failure Rate vs Users
- **Use**: Capacity planning and bottleneck identification

**Response Time vs Users** 📈:
- **Shows**: Clean scaling plot with one line per iteration
- **Format**: Professional chart suitable for presentations
- **Use**: Stakeholder reports and SLA validation

### **Reading the Graphs**

**Response Time Trends:**
- 📊 **Flat line**: System handles load well
- 📈 **Gradual increase**: Normal degradation under load  
- 🚀 **Sharp increase**: System reaching capacity limits
- 📊 **Erratic spikes**: Resource contention or bottlenecks

**Failure Rate Analysis:**
- ✅ **0%**: Perfect reliability
- 🟡 **1-3%**: Good for healthcare applications
- 🟠 **3-5%**: Acceptable but investigate
- 🔴 **>5%**: Unacceptable for healthcare - fix required

**Throughput Patterns:**
- 📈 **Linear increase**: Good scalability
- 📊 **Plateau**: System reaching maximum capacity
- 📉 **Decrease**: System becoming overloaded

---

## ⚡ Performance Thresholds

### **Healthcare Application Standards**
```
✅ Excellent: <1% error rate, <500ms avg response
🟡 Good:      1-3% error rate, 500-1000ms avg response  
🟠 Acceptable: 3-5% error rate, 1000-2000ms avg response
🔴 Poor:       >5% error rate, >2000ms avg response
```

### **OralSmart Specific Targets**
- **Average Response Time**: <1000ms for patient operations
- **95th Percentile**: <2000ms under normal load
- **Throughput**: >10 RPS per server instance
- **Failure Rate**: <1% for patient data operations
- **Concurrent Users**: Support 50+ healthcare professionals

### **Enhanced Load Test Thresholds**
Default acceptable thresholds (configurable):
- **Average Response Time**: < 2000ms
- **P95 Response Time**: < 5000ms  
- **Failure Rate**: < 5%
- **Minimum RPS**: > 1.0 requests/second

### **Bottleneck Indicators**
🔍 **Look for these warning signs:**
- Response time >2x increase when doubling users
- Failure rate >1% under normal load
- Throughput plateau or decrease with more users
- Memory/CPU spikes correlating with performance drops

---

## 🔧 Troubleshooting

### **Common Issues & Solutions**

#### **❌ "Connection refused" Errors**
```
Problem: Cannot connect to http://localhost:8000
Solution: 
1. cd src && python manage.py runserver
2. Verify server responds: curl http://localhost:8000
3. Check for port conflicts
```

#### **❌ "No valid results obtained from testing"**
```
Problem: CSV files not generated or empty
Solutions:
1. Check Django server is running and responsive
2. Verify test user exists: username=testuser, password=testpass123
3. Run with lower user count first: --users 5
4. Check loadtesting/setup_test_data.py was run
```

#### **❌ "HTTPError: 404 Client Error"**
```
Problem: Specific URLs returning 404
Solutions:
1. Check Django URL patterns in src/oralsmart/urls.py
2. Verify test data exists (patients, users)
3. Run: python manage.py migrate
4. Check the analyze_error_breakdown.py output to identify failing endpoints
```

#### **❌ Import Errors (matplotlib, seaborn, etc.)**
```
Problem: Missing dependencies for enhanced testing
Solution: pip install -r requirements-loadtest.txt
```

#### **❌ High Failure Rates (>10%)**
```
Problem: System overload or configuration issues
Solutions:
1. Reduce user count: --users 10
2. Check server resources (CPU/Memory)
3. Verify database connections
4. Review Django DEBUG settings
5. Check for database migration issues
```

### **Enhanced Load Testing Specific Issues**

#### **❌ "Scenarios not running in sequence"**
```
Problem: Enhanced tests stopping after first scenario
Solutions:
1. Check available memory - multiple scenarios need resources
2. Reduce iterations: --iterations 1
3. Run scenarios individually: --scenarios light_load
```

#### **❌ "Graphs not generating"**
```
Problem: Missing graph files in output
Solutions:
1. Verify matplotlib/seaborn installation
2. Check disk space in reports directory
3. Run with --check-server to verify connectivity
4. Try single scenario first: --scenarios quick_test
```

### **Performance Debugging Steps**

1. **Start Small**: Always test with 5-10 users first
2. **Check Logs**: Monitor Django console for errors during tests
3. **Verify Data**: Ensure test data exists and is accessible
4. **Incremental Scale**: Gradually increase user count to find breaking point
5. **Analyze Patterns**: Use error breakdown script to identify problematic endpoints

### **Getting Help**

**Debug Scripts Available:**
```bash
# Check server connectivity
python loadtesting/test_server_connectivity.py

# Setup verification
python loadtesting/check_setup.py

# Analyze specific error patterns (after tests)
python loadtesting/analyze_error_breakdown.py
```

**Test Data Verification:**
```bash
# Verify test users exist
python src/manage.py shell
>>> from django.contrib.auth.models import User
>>> User.objects.filter(username__startswith='testuser').count()
# Should return 5
```

---

## 📝 Best Practices

### **For Development**
- Start with `enhanced_load_test.py --scenarios quick_test` for rapid feedback
- Use `--users 5-10` for initial testing
- Run `setup_test_data.py` after database changes

### **For QA/Staging**
- Use scaling tests: `--user-range "10-50-10"`
- Use enhanced load testing for comprehensive validation
- Target 3x expected production load
- Validate all failure rates <1%

### **For Production Validation**
- Test with realistic user counts (100-500+)
- Use both enhanced and virtual user testing
- Generate professional reports for stakeholders
- Document performance baselines for regression testing

### **Continuous Integration**
```bash
# Quick CI performance gate
python loadtesting/enhanced_load_test.py --scenarios quick_test --iterations 1

# Comprehensive nightly performance validation
python loadtesting/enhanced_load_test.py --scenarios light_load moderate_load --iterations 3
```

---

## 🎉 Success Criteria

**Your OralSmart application is ready for production when:**

✅ **Scaling Test**: Response time increases <2x when users double  
✅ **Reliability**: <1% failure rate under expected load  
✅ **Performance**: <1000ms average response time for patient operations  
✅ **Capacity**: Handles 2x expected peak concurrent users  
✅ **Stability**: Consistent performance across 3+ test iterations  
✅ **Load Patterns**: All enhanced load test scenarios pass thresholds

---

**Need more help?** Check the specific test runner files for advanced options or create an issue with your test results for debugging assistance.