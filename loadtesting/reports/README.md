# Load Testing Reports Directory

This directory contains load testing reports and results from OralSmart load testing.

**📖 For complete load testing instructions, see:** [`../COMPLETE_LOAD_TESTING_GUIDE.md`](../COMPLETE_LOAD_TESTING_GUIDE.md)

## Enhanced Testing Output 

When using the enhanced load testing script (`enhanced_load_test.py`), test results are organized by timestamp:

**📖 For complete enhanced load testing instructions, see the [Complete Load Testing Guide](../COMPLETE_LOAD_TESTING_GUIDE.md#enhanced-load-testing---detailed-usage)**

```
reports/
├── test_run_20241019_143022/          # Timestamped test run directory
│   ├── light_load_performance_graphs.png       # 4-panel performance overview
│   ├── light_load_detailed_response_times.png  # Detailed response time trends
│   ├── moderate_load_performance_graphs.png    # Performance graphs for moderate load
│   ├── moderate_load_detailed_response_times.png
│   ├── heavy_load_performance_graphs.png       # Performance graphs for heavy load
│   ├── heavy_load_detailed_response_times.png
│   ├── scenarios_comparison.png                # Comparison across all scenarios
│   ├── load_test_summary.md                   # Comprehensive text report
│   └── *.csv, *.html                          # Raw Locust reports
```

## Graph Types Generated

### 1. Performance Overview Graphs (`*_performance_graphs.png`)
Four-panel graphs for each scenario showing:
- **Average Response Time vs Users** - How response time scales with user load
- **95th Percentile Response Time vs Users** - P95 response times (high percentiles)
- **Requests per Second vs Users** - Throughput scaling
- **Failure Rate vs Users** - Error rates under different loads

### 2. Detailed Response Time Graphs (`*_detailed_response_times.png`)
Shows individual iteration results plus average trend line:
- Individual lines for each iteration
- Bold average line across all iterations
- Annotations for key performance points
- Error bars showing variability

### 3. Scenario Comparison Graph (`scenarios_comparison.png`)
Compares all tested scenarios on a single graph:
- Response time comparison across scenarios
- Shows which scenario performs better under load
- Useful for understanding system behavior patterns

## Test Scenarios

### Light Load
- **Users**: 1, 3, 5, 8, 10 concurrent users
- **Focus**: Read-heavy operations (browsing, viewing)
- **Duration**: 3 minutes per test
- **Use case**: Normal daily usage patterns

### Moderate Load  
- **Users**: 10, 15, 20, 25, 30 concurrent users
- **Focus**: Mixed operations (create, read, update)
- **Duration**: 3 minutes per test
- **Use case**: Peak usage periods

### Heavy Load
- **Users**: 20, 30, 40, 50, 60 concurrent users
- **Focus**: Intensive operations (reports, ML predictions)
- **Duration**: 4 minutes per test  
- **Use case**: Stress testing and capacity planning

## Key Metrics Tracked

- **Average Response Time**: Mean response time across all requests
- **95th Percentile (P95)**: Response time for the slowest 5% of requests
- **99th Percentile (P99)**: Response time for the slowest 1% of requests
- **Requests per Second (RPS)**: System throughput
- **Failure Rate**: Percentage of failed requests
- **Total Requests**: Volume of requests processed

## Running Enhanced Tests

### Quick Start
```bash
# Run all scenarios with 3 iterations each
python loadtesting/enhanced_load_test.py --iterations=3

# Run specific scenarios
python loadtesting/enhanced_load_test.py --scenarios light_load moderate_load --iterations=5

# Use the launcher (Windows)
loadtesting/run_load_tests.bat

# Use the launcher (Cross-platform)
python loadtesting/run_load_tests.py
```

### Command Line Options
- `--host`: Target server (default: http://localhost:8000)
- `--iterations`: Number of test iterations per scenario (default: 3)
- `--scenarios`: Specific scenarios to run (default: all)
- `--check-server`: Verify server is running before testing

## Standard Locust Output (Legacy)

- `load_test_report.html` - Standard Locust HTML report
- `load_test_stats_*.csv` - Raw statistics in CSV format
- Individual test HTML/CSV files

## Interpreting Results

### Response Time Trends
- **Flat line**: System handles load well
- **Gradual increase**: Normal degradation under load
- **Sharp increase**: System reaching capacity limits
- **Spikes/irregularity**: Potential bottlenecks or resource contention

### Failure Rate Analysis
- **0% failure rate**: System stable under test load
- **<5% failure rate**: Acceptable for most applications  
- **>5% failure rate**: Investigate bottlenecks or scaling issues
- **High failure rate**: System overloaded or configuration issues

### Throughput Patterns
- **Linear increase**: Good scalability
- **Plateau**: System reaching maximum capacity
- **Decrease**: System becoming overloaded

## Performance Thresholds

Default acceptable thresholds (configurable in `enhanced_locust.conf`):
- Average Response Time: < 2000ms
- P95 Response Time: < 5000ms  
- Failure Rate: < 5%
- Minimum RPS: > 1.0 requests/second