# OralSmart Deployment & Security Guide

This document covers Docker-based deployment and security testing for OralSmart.

---

## Table of Contents
1. [Deployment Architecture](#1-deployment-architecture)
2. [Quick Start](#2-quick-start)
3. [Configuration](#3-configuration)
4. [Management Commands](#4-management-commands)
5. [Testing Deployment](#5-testing-deployment)
6. [Security Configuration](#6-security-configuration)
7. [Security Testing](#7-security-testing)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Deployment Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   Nginx     │────│ Django App   │────│   MySQL     │
│ (Port 80)   │    │ (Port 8000)  │    │ (Port 3306) │
└─────────────┘    └──────────────┘    └─────────────┘
       │                   │
   ┌───▼────┐          ┌───▼────┐    ┌────────┐
   │ Static │          │ Redis  │    │ Volume │
   │ Files  │          │ Cache  │    │  Data  │
   └────────┘          └────────┘    └────────┘
```

**Prerequisites:**
- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Docker Compose v2.0+
- 4 GB RAM minimum
- 2 GB free disk space

**Key features:** GPU support (CUDA), Gunicorn auto-scaling, Nginx load balancing, health check endpoints, MySQL with persistent storage, non-root containers, rate limiting.

**File structure:**
```
oralsmart/
├── Dockerfile.prod          # Production container
├── docker-compose.yml       # Development setup
├── docker-compose.prod.yml  # Production setup
├── requirements-prod.txt
├── .env.example
├── deploy.sh / deploy.bat
├── .dockerignore
└── docker/nginx/nginx.conf
```

---

## 2. Quick Start

### 1. Setup Environment

```bash
cd /path/to/oralsmart
cp .env.example .env
# Edit .env with your settings
notepad .env   # Windows
nano .env      # Linux/Mac
```

### 2. Deploy

**Windows:**
```batch
deploy.bat
```

**Linux/Mac:**
```bash
chmod +x deploy.sh && ./deploy.sh
```

**Manual:**
```bash
docker-compose build
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

### 3. Access

| Endpoint | URL |
|----------|-----|
| Web App  | http://localhost:8000 |
| Admin    | http://localhost:8000/admin |
| Health   | http://localhost:8000/health/ |
| ML API   | http://localhost:8000/ml/ |

### Development vs Production

```bash
# Development (debug mode, SQLite option, hot reload)
docker-compose up -d

# Production (Nginx, MySQL, Redis, SSL-ready, performance-optimized)
docker-compose -f docker-compose.prod.yml up -d
```

---

## 3. Configuration

### Environment Variables (`.env`)

```bash
# Database
DB_NAME=oralsmart
DB_USER=oralsmart
DB_PASSWORD=your-secure-password
DB_HOST=db
DB_PORT=3306

# Django
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,your-domain.com

# ML Models
USE_GPU=True
MODEL_PATH=/app/ml_models/saved_models

# Redis
REDIS_URL=redis://redis:6379/0

# Email (for referral notifications)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_PORT=587
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=OralSmart <noreply@oralsmart.com>
SITE_URL=https://your-domain.com

# Referrals
REFERRAL_EXPIRY_DAYS=30
REFERRAL_MAX_RETRY_ATTEMPTS=3
```

### Production Scaling (docker-compose.prod.yml)

```yaml
services:
  web:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
```

### SSL/TLS Setup

```bash
# Self-signed (development)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout docker/ssl/server.key -out docker/ssl/server.crt

# Let's Encrypt (production)
certbot certonly --standalone -d your-domain.com
```

---

## 4. Management Commands

### Service Management

```bash
docker-compose up -d                    # Start
docker-compose down                     # Stop
docker-compose logs -f                  # View logs
docker-compose logs -f --tail=100       # Live tail
docker-compose restart web              # Restart specific service
docker-compose build --no-cache         # Rebuild
docker-compose ps                       # Service status
docker stats                            # Resource usage
```

### Django Management (in container)

```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py collectstatic
docker-compose exec web python manage.py train_ml_model
docker-compose exec web python manage.py shell
```

### Database Management

```bash
# Access DB shell
docker-compose exec db mysql -u oralsmart -p oralsmart

# Backup
docker-compose exec db mysqldump -u oralsmart -p oralsmart > backup.sql

# Restore
docker-compose exec -T db mysql -u oralsmart -p oralsmart < backup.sql
```

### Automated Retry (Referrals)

```bash
# Run manually
python manage.py retry_failed_referrals

# Schedule with Celery Beat (production)
# In settings.py:
CELERY_BEAT_SCHEDULE = {
    'retry-failed-referrals': {
        'task': 'referrals.tasks.retry_failed_referrals',
        'schedule': crontab(minute=0, hour='*/1'),
    },
}
```

---

## 5. Testing Deployment

### Health Check

```bash
curl http://localhost:8000/health/
# Expected:
# {"status": "healthy", "services": {"database": "healthy", "ml_models": "loaded", ...}}
```

### ML Model Test

```bash
curl -X POST http://localhost:8000/ml/predict/ \
  -H "Content-Type: application/json" \
  -d '{"dental_data": {...}, "dietary_data": {...}}'
```

### Load Test

```bash
ab -n 100 -c 10 http://localhost:8000/
```

### CI/CD Integration

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy
        run: ssh user@server 'cd /app && docker-compose -f docker-compose.prod.yml up -d'
```

---

## 6. Security Configuration

### Django Security Settings

```python
# settings.py — verify these are set for production

# 1. Debug and Secret Key
DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY')

# 2. HTTPS and Security Headers
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# 3. Session Security
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# 4. CSRF Protection
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# 5. Allowed Hosts
ALLOWED_HOSTS = ['your-domain.com']
```

### Security Middleware

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django_ratelimit.middleware.RatelimitMiddleware',  # Add rate limiting
    'django_csp.middleware.CSPMiddleware',              # Add CSP headers
    # ... existing middleware
]
```

### Nginx Security Headers

The `docker/nginx/nginx.conf` includes:
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `X-XSS-Protection: 1; mode=block`
- Rate limiting on API endpoints

### Referral System Security

- 256-bit random access tokens
- 30-day time-limited portal links
- View count tracking
- Optional PIN authentication
- CSRF protection on all forms
- Role-based permission checks

---

## 7. Security Testing

### Test Categories

#### 1. Authentication & Session Security (`test_security_auth.py`)
| Test | Security Risk |
|------|--------------|
| `test_password_complexity_enforcement` | Weak authentication |
| `test_session_timeout_behavior` | Session hijacking |
| `test_brute_force_protection` | Brute force attacks |
| `test_concurrent_session_handling` | Session management |
| `test_redirect_after_login` | Open redirect |
| `test_user_enumeration_protection` | Information disclosure |

#### 2. CSRF Protection (`test_security_csrf.py`)
| Test | Security Risk |
|------|--------------|
| `test_csrf_token_presence_in_forms` | CSRF attacks |
| `test_csrf_protection_on_post_requests` | CSRF attacks |
| `test_csrf_token_in_ajax_requests` | CSRF attacks |
| `test_referer_header_validation` | CSRF attacks |

#### 3. Input Validation & Injection (`test_security_injection.py`)
| Test | Security Risk |
|------|--------------|
| `test_sql_injection_protection` | Data breach |
| `test_xss_protection` | XSS attacks |
| `test_file_upload_security` | Code execution |
| `test_path_traversal_protection` | File system access |
| `test_command_injection_protection` | System compromise |
| `test_header_injection_protection` | Header manipulation |

#### 4. Authorization & Access Control (`test_security_access_control.py`)
| Test | Security Risk |
|------|--------------|
| `test_unauthorized_access_protection` | Unauthorized access |
| `test_user_data_isolation` | Data leakage |
| `test_admin_area_protection` | Privilege escalation |
| `test_direct_object_reference_protection` | Unauthorized data access (IDOR) |
| `test_privilege_escalation_protection` | Privilege escalation |
| `test_account_lockout_protection` | Brute force |

#### 5. Data Protection & Privacy (`test_security_data_protection.py`)
| Test | Security Risk |
|------|--------------|
| `test_sensitive_data_not_in_source` | Information disclosure |
| `test_http_security_headers` | Various attacks |
| `test_cookie_security_attributes` | Session hijacking |
| `test_personal_data_protection` | Privacy breach |
| `test_data_export_security` | Data breach |

#### 6. Business Logic Tests (Application-specific)
- Patient data access controls
- Medical report authorization
- ML model input validation
- Assessment form tampering protection
- Age-based restriction validation

### Running Security Tests

```bash
# Install dependencies
pip install pytest playwright pytest-django

# Install Playwright browsers
python -m playwright install

# Run all security tests
pytest tests/e2e/test_security_*.py -v -m security

# Run specific category
pytest tests/e2e/test_security_auth.py -v
pytest tests/e2e/test_security_csrf.py -v
pytest tests/e2e/test_security_injection.py -v
pytest tests/e2e/test_security_access_control.py -v
pytest tests/e2e/test_security_data_protection.py -v

# Generate HTML report
pytest tests/e2e/test_security_*.py --html=security_report.html --self-contained-html
```

### Security Test Coverage Goals

| Domain | Target Coverage |
|--------|----------------|
| Authentication flows | 95%+ |
| Access controls | 100% |
| User inputs | 90%+ |
| Sensitive data handling | 100% |

### Security Maintenance Schedule

| Frequency | Activity |
|-----------|----------|
| Monthly | Review/update test data |
| Quarterly | Add tests for new features |
| Annually | Comprehensive security audit |
| Ongoing | Dependency vulnerability scanning |

### Penetration Testing Tools

- **OWASP ZAP** – Automated security scanner
- **Burp Suite** – Manual penetration testing
- **SQLmap** – SQL injection testing
- **securityheaders.com** – Security header validation

---

## 8. Troubleshooting

### Common Deployment Issues

| Problem | Solution |
|---------|----------|
| Port already in use | `netstat -tulpn \| grep :8000` then kill the PID |
| Database connection failed | `docker-compose logs db`, then `docker-compose down -v && docker-compose up -d` |
| ML model loading error | `docker-compose exec web ls /app/ml_models/saved_models/` or retrain |
| Permission denied | `sudo chown -R $(whoami):$(whoami) . && chmod +x deploy.sh` |
| Out of memory | `docker system prune -a`, increase Docker memory limit |

### Log Analysis

```bash
docker-compose logs web      # App logs
docker-compose logs db       # DB logs
docker-compose logs nginx    # Nginx logs
```

### Cloud Deployment (AWS/Azure/GCP)

1. Setup cloud infrastructure (VM/container service)
2. Configure environment variables as secrets
3. Deploy with `docker-compose.prod.yml`
4. Setup domain and SSL (Let's Encrypt)
5. Configure monitoring and alerting

---

*For additional support: check logs (`docker-compose logs -f`), verify the health endpoint, and ensure ML models are present in `saved_models/`.*
