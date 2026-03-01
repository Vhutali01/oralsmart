# OralSmart ML & Clinical Guide

This document consolidates all information about the ML model, training dataset, and clinical risk assessment algorithm.

---

## Table of Contents
1. [Clinical Risk Assessment Algorithm](#1-clinical-risk-assessment-algorithm)
2. [Dataset Documentation](#2-dataset-documentation)
3. [ML Model Training](#3-ml-model-training)
4. [Complete ML Workflow](#4-complete-ml-workflow)

---

## 1. Clinical Risk Assessment Algorithm

Evidence-based oral health risk scoring for pediatric patients using established clinical risk factors.

### Risk Scoring

#### Major Clinical Findings (+2 points each)
- **Cavitated lesions** – Active caries requiring intervention
- **Missing teeth** – Evidence of severe disease progression
- **Multiple restorations** – History of high caries activity
- **Enamel changes** – Demineralization (early caries process)
- **Dentin discoloration** – Advanced caries penetration
- **White spot lesions** – Early reversible caries lesions

#### Dietary Risk Factors (+1 point each)
- **Sweet/sugary foods** – Primary substrate for cariogenic bacteria
- **Processed foods** – High in added sugars and refined carbohydrates
- **Sugar-sweetened beverages** – High sugar with frequent exposure
- **Processed fruit products** – Added sugars increase cariogenic potential
- **Frequency modifier** – +1 additional point for ≥3 times daily consumption

#### Protective Factors (-1 point each)
- **Fluoride water** – Community water fluoridation
- **Fluoride toothpaste** – Daily topical fluoride exposure
- **Professional topical fluoride** – Clinical fluoride applications
- **Regular dental checkups** – Early detection and prevention
- **Pit and fissure sealants** – Physical occlusal surface protection

### Risk Classification Thresholds

**Standard:**
| Risk Level | Score Range | Recommendation |
|------------|-------------|----------------|
| High Risk  | ≥ 8.0       | Immediate intervention |
| Medium Risk | 5.2 – 7.9  | Regular monitoring, follow-up in 3–6 months |
| Low Risk   | < 5.2       | Continue preventive care, regular check-ups |

**Adaptive Thresholds** (adjust based on data completeness):
| Data Available      | High Threshold | Medium Threshold |
|---------------------|----------------|------------------|
| Complete assessments | 8.0           | 5.2              |
| Single assessment    | 6.0           | 3.9              |
| Minimal data         | 4.0           | 2.6              |

### Clinical Evidence Base
- Stephan curve research (frequency vs. quantity impact)
- Community water fluoridation effectiveness studies
- Caries process progression (demineralization to cavitation)
- Evidence-based preventive intervention outcomes

---

## 2. Dataset Documentation

### Overview

> ⚠️ **Important**: The ML model is trained entirely on **synthetic data** – no real patient data is used.

| Property | Value |
|----------|-------|
| Primary file | `balanced_3class_training_data.csv` |
| Size | 7,007 records |
| Features | 68 features + 1 target (`risk_level`) |
| Classes | 3 (low / medium / high risk) |
| Balance | ~33.3% per class |

**Benefits of synthetic data:**
- **Privacy** – No real patient PII
- **Reproducibility** – Consistent via defined distributions
- **Scalability** – Generate any size dataset
- **Balance** – Equal class distribution prevents model bias

### South African Demographic Alignment

The dataset reflects South African pediatric demographics (ages 0–6):

**Age distribution:**
| Age | Weight | Percentage |
|-----|--------|------------|
| 0   | 0.25   | 25% |
| 1   | 0.23   | 23% |
| 2   | 0.17   | 17% |
| 3   | 0.12   | 12% |
| 4   | 0.10   | 10% |
| 5   | 0.08   | 8%  |
| 6   | 0.05   | 5%  |

**Gender:** 50% Male / 50% Female

**SA-specific fields:**
- `sa_citizen` – 50% probability
- `special_needs` – ~8% probability
- `fluoride_water` – ~65% probability (SA water fluoridation coverage)

### Data Generation Methodology

Three interconnected factory classes (in `src/patient/factory.py` and `src/assessments/factory.py`):

#### 1. Patient Factory
Generates: name, surname (gender-appropriate), age, gender, parent/guardian info.

#### 2. Dental Screening Factory (32 features)

**Risk factors (binomial distributions):**
| Factor | Probability |
|--------|-------------|
| Plaque presence | 40% |
| Dry mouth | 20% |
| Enamel defects | 40% |
| Special needs | 8% |
| White spot lesions | 40% |
| Cavitated lesions | 30% |
| Multiple restorations | 30% |
| Missing teeth | 30% |

**Protective factors:**
| Factor | Probability |
|--------|-------------|
| Fluoride water access | 65% |
| Fluoride toothpaste use | 80% |
| Topical fluoride treatment | 60% |
| Regular dental checkups | 70% |
| Sealed pits and fissures | 60% |

**Clinical findings:** Teeth status for 20 primary teeth (FDI: 51–65, 71–85), DMFT scoring.

#### 3. Dietary Screening Factory (35 features)

Food categories: sweet/sugary foods, takeaways, fresh fruit, cold drinks/juices, processed fruit, spreads, added sugars, salty snacks, dairy, vegetables, water.

For each: consumption (yes/no), daily frequency, weekly frequency, timing, bedtime consumption (cariogenic foods).

#### Risk-Based Probability Adjustments

**Dental risk weights:**
| Factor | Weight |
|--------|--------|
| Special needs | 3.5 |
| Plaque, enamel defects, cavitated lesions | 3.0 each |
| Dry mouth | 2.0 |
| Lack of fluoride | 2.0–2.5 |

**Dietary risk:** higher for between-meal and bedtime consumption; lower for protective foods (water, dairy, vegetables).

#### Age-Specific Tooth Development

| Age Group | Characteristic |
|-----------|---------------|
| < 1 year  | 88% unerupted teeth, 2% ECC |
| 1–2 years | Erupting primary teeth, ~8% ECC |
| 2–4 years | Full primary dentition forming, 20–28% decayed teeth |
| 5–6 years | Established primary dentition, beginning mixed dentition |

### Dataset Features (68 Total)

**Dental Screening (32):** special_needs, caregiver_treatment, appliance, plaque, dry_mouth, enamel_defects, fluoride_water, fluoride_toothpaste, topical_fluoride, regular_checkups, sealed_pits, restorative_procedures, enamel_change, dentin_discoloration, white_spot_lesions, cavitated_lesions, multiple_restorations, missing_teeth, total_dmft_score, + 13 tooth-status fields (FDI codes).

**Dietary Screening (35):** 11 food categories × consumption/frequency/timing fields.

**Demographic (1):** `sa_citizen`

**Target:** `risk_level` (low / medium / high)

### Dataset Balance & Quality

| Risk Level | Records | Percentage |
|------------|---------|------------|
| Low        | ~2,335  | 33.3% |
| Medium     | ~2,336  | 33.3% |
| High       | ~2,336  | 33.3% |

**Missing data patterns:** ~65% have both assessments, ~20% dental only, ~15% dietary only.

**Data validity:** Binary fields (yes/no), predefined frequency categories, DMFT 0–20, tooth status FDI codes (A, B, C, D, E, X, F).

### Limitations

1. **Not real patient data** – probability distributions, not clinical observations
2. **Simplified relationships** – real-world complexity may not be fully captured
3. **South African context** – clinical risk factors need local epidemiological validation
4. **Requires clinical validation** before production deployment with real patients

---

## 3. ML Model Training

### Quick Start

```bash
cd src
```

#### Training Modes

| Mode | Command | Time | Accuracy | Use Case |
|------|---------|------|----------|----------|
| **Production (Full)** | `python manage.py train_ml_model balanced_3class_training_data.csv` | 10–30 min | ~87% | Production |
| **Fast (Dev)** | `... --fast` | 2–5 min | ~87% | Development |
| **Baseline (Test)** | `... --baseline` | 1–2 min | ~87% | Quick testing |

#### Feature Selection Methods

```bash
# Random Forest importance (default, recommended for medical data)
python manage.py train_ml_model data.csv --feature-selection-method importance --n-features 40

# ANOVA F-statistic (fast, reliable)
python manage.py train_ml_model data.csv --feature-selection-method kbest --n-features 30

# Recursive Feature Elimination (most thorough, slowest)
python manage.py train_ml_model data.csv --feature-selection-method rfe --n-features 35
```

#### Disable Specific Enhancements

```bash
python manage.py train_ml_model data.csv --no-hyperparameter-tuning
python manage.py train_ml_model data.csv --no-feature-selection
python manage.py train_ml_model data.csv --no-hyperparameter-tuning --no-feature-selection  # fastest
```

### Data Management Commands

```bash
# Generate synthetic patients
python manage.py create_patients --count 1000 --assessment-pattern mixed

# Assessment patterns: mixed (65% both / 20% dental / 15% dietary), both, dental-only, dietary-only

# Export to CSV
python manage.py export_training_data --output my_data.csv
python manage.py export_plain_csv output.csv  # system encoding

# SAFE: Clear patients only (keeps users)
python manage.py clear_patients
python manage.py clear_patients --confirm    # skip prompt

# DANGER: Clear everything including users
python manage.py create_patients --clean
```

| Command | Deletes Patients | Deletes Assessments | Deletes Users |
|---------|:---:|:---:|:---:|
| `clear_patients` | YES | YES | NO ✅ |
| `create_patients --clean-patients` | YES | YES | NO ✅ |
| `create_patients --clean` | YES | YES | YES ⚠️ |

### Testing & Validation

```bash
python manage.py test_ai_integration
python manage.py train_ml_model --help
```

### Model Details

- **Algorithm:** MLPClassifier (Neural Network) with optimized hyperparameters
- **Feature Selection:** Reduces 68 features to 30–40 most important
- **Cross-Validation:** 5-fold stratified validation
- **Hyperparameter Tuning:** GridSearchCV optimization

### Expected Training Output

```
Starting Enhanced ML Training Pipeline
Dataset: balanced_3class_training_data.csv (7007 samples, 68 features)

Feature Selection (Random Forest Importance)
   → Selected 40 best features
   → Top features: cavitated_lesions, multiple_restorations, white_spot_lesions

Hyperparameter Tuning (GridSearchCV)
   → Testing 24 parameter combinations
   → Best params: {'hidden_layer_sizes': (100, 50), 'alpha': 0.001}

Cross-Validation Results:
   → Accuracy: 87.3% (±2.1%)
   → Precision: 86.8% | Recall: 87.1% | F1: 86.9%

Model saved to: ml_models/saved_models/
Training completed in ~15 minutes
```

### Troubleshooting Training

| Problem | Solution |
|---------|----------|
| "No training data found" | `python manage.py create_patients --count 500 && python manage.py export_training_data` |
| Training too slow | Use `--fast` or reduce `--n-features 20` |
| Low accuracy | Use full mode with more data (`--count 2000`) |
| Memory issues | `--n-features 25 --no-hyperparameter-tuning` |

---

## 4. Complete ML Workflow

### Step 1: Setup

```bash
git clone https://github.com/vhutali01/oralsmart.git
cd oralsmart
python -m venv venv
.\venv\Scripts\activate       # Windows
# source venv/bin/activate    # Mac/Linux
pip install -r requirements.txt
cd src
python manage.py migrate
```

### Step 2: Training Data

```bash
# Option A: Use pre-balanced dataset (recommended)
# balanced_3class_training_data.csv is already included

# Option B: Generate fresh
python manage.py create_patients --count 1500 --force
python manage.py export_training_data --output fresh_training_data.csv
```

### Step 3: Train

```bash
# Production
python manage.py train_ml_model balanced_3class_training_data.csv

# Development (faster)
python manage.py train_ml_model balanced_3class_training_data.csv --fast
```

### Step 4: Validate

```bash
python manage.py test_ai_integration
```

### Step 5: Run

```bash
python manage.py runserver
# Visit http://127.0.0.1:8000
```

### Production Training Checklist

```bash
# 1. Clean existing patient data (safe – keeps users)
python manage.py clear_patients --confirm

# 2. Generate large balanced dataset
python manage.py create_patients --count 2000 --assessment-pattern mixed --force

# 3. Export
python manage.py export_training_data --output production_data.csv

# 4. Train with full enhancements
python manage.py train_ml_model production_data.csv

# 5. Validate
python manage.py test_ai_integration
```

Pre-deployment checks:
- [ ] Model accuracy > 85%
- [ ] AI integration test passes
- [ ] Report generation works
- [ ] Validated with dental professional

---

*Last Updated: December 2025 | Dataset Version: Balanced 3-Class v1.0*
