# OralSmart

OralSmart is a Django web application for pediatric oral health risk assessment with AI-powered predictions. It provides comprehensive dental and dietary screening with machine learning-based risk classification for healthcare professionals.

## Key Features

- **Patient Management** – Registration and demographic tracking
- **Comprehensive Screening** – Dental and dietary assessments with save-as-draft
- **AI Risk Assessment** – 3-class prediction (Low / Medium / High risk)
- **Dual Report System** – Patient-friendly and professional versions with PDF export
- **Referral System** – Multi-method delivery (email, API, SMS, portal) with audit trails
- **In-App Notifications** – Real-time referral alerts with bell icon and badge counter
- **ML Model Training** – Advanced feature selection and hyperparameter tuning
- **Clinical Decision Support** – Evidence-based recommendations

## Documentation

| Document | Contents |
|----------|----------|
| [ML_AND_CLINICAL_GUIDE.md](ML_AND_CLINICAL_GUIDE.md) | Clinical risk algorithm, synthetic dataset details, ML training commands, complete workflow |
| [REFERRALS_AND_NOTIFICATIONS.md](REFERRALS_AND_NOTIFICATIONS.md) | Referral system setup, delivery methods, in-app notifications, API endpoints |
| [DEPLOYMENT_AND_SECURITY.md](DEPLOYMENT_AND_SECURITY.md) | Docker deployment, environment config, security settings, security testing |
| [USER_GUIDE.md](USER_GUIDE.md) | Application features, usability improvements, test practitioner accounts |
| [tests/README.md](tests/README.md) | E2E testing framework, test suites, running instructions |
| [docs/flowcharts/oralsmart_mini_flowcharts.md](docs/flowcharts/oralsmart_mini_flowcharts.md) | Mermaid flowcharts for auth, screening, and referral flows |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, Django 3.2.25 |
| Database | SQLite (dev) / MySQL (prod) |
| ML | MLPClassifier (scikit-learn), Neural Network |
| Cache | Redis |
| Frontend | HTML/CSS (Django templates), Bootstrap 5 |
| Container | Docker, Nginx, Gunicorn |

## Quick Setup

```bash
# 1. Clone and create environment
git clone https://github.com/vhutali01/oralsmart.git
cd oralsmart
python -m venv venv
.\venv\Scripts\activate     # Windows
# source venv/bin/activate  # Mac/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup database
cd src
python manage.py migrate

# 4. (Optional) Train ML model
python manage.py train_ml_model balanced_3class_training_data.csv

# 5. Run
python manage.py runserver
```

Visit http://127.0.0.1:8000

## AI Risk Assessment

> ⚠️ The ML model is trained on **synthetic data** aligned with South African pediatric demographics (ages 0–6). Clinical validation with real patient data is required before clinical deployment.

- **Dataset:** 7,007 balanced synthetic records, 68 features
- **Model:** MLPClassifier (~87% accuracy with full training mode)
- **Classes:** Low / Medium / High risk
- **Reports:** Dual system — patient-friendly (no AI data) and professional (full analysis)

See [ML_AND_CLINICAL_GUIDE.md](ML_AND_CLINICAL_GUIDE.md) for training commands, dataset details, and clinical scoring algorithm.

## Data Management

```bash
cd src

# SAFE: Clear patients only (keeps user accounts)
python manage.py clear_patients

# Generate synthetic test data
python manage.py create_patients --count 1000 --assessment-pattern mixed

# Export training data
python manage.py export_training_data --output training_data.csv
```

## Docker Deployment

```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.prod.yml up -d
```

See [DEPLOYMENT_AND_SECURITY.md](DEPLOYMENT_AND_SECURITY.md) for full deployment and security configuration.

## Referral System

Multi-method patient referral management with intelligent routing:

```bash
# Required: run migrations
python manage.py makemigrations facility referrals
python manage.py migrate
```

See [REFERRALS_AND_NOTIFICATIONS.md](REFERRALS_AND_NOTIFICATIONS.md) for complete setup and usage.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes
4. Open a Pull Request

## License

MIT License – see LICENSE file for details.

---

*OralSmart – AI-Powered Pediatric Oral Health Risk Assessment*
