# CodeCraft — Early Metabolic Risk Detection Platform
### Benchmark Comparison of Classical ML vs Deep Learning vs Quantum ML on NHANES 2017–2018

[![CodeCraft Continuous Integration](https://github.com/PES1UG24AM004/SE-Mini-Project/actions/workflows/ci.yml/badge.svg)](https://github.com/PES1UG24AM004/SE-Mini-Project/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MLflow 3.x](https://img.shields.io/badge/MLflow-3.x-0194E2.svg)](https://mlflow.org/)
[![License: Academic Research](https://img.shields.io/badge/License-Academic_Research-lightgrey.svg)](README.md)

> **Academic Research & Educational Use Disclaimer:**  
> **Research/educational use only. Not a diagnosis or medical advice.**  
> This platform implements a cross-sectional classification benchmark within the NHANES 2017–2018 survey cycle. It does not predict future disease incidence or clinical onset.

---

## 1. Project Overview

The **CodeCraft Early Metabolic Risk Detection Platform** is a local-first, privacy-preserving research website built for the Software Engineering Mini-Project at PES University. The application benchmarks three distinct modeling paradigms on held-out records from the **NHANES 2017–2018** cycle:

1. **Classical Machine Learning (ML):** `HistGradientBoostingClassifier` (scikit-learn) with balanced sample weighting.
2. **Deep Learning (DL):** Feed-forward Multi-Layer Perceptron (PyTorch) with dropout, Adam optimizer, positive class loss weighting, and validation early stopping.
3. **Quantum Machine Learning (QML):** Variational Quantum Classifier (PennyLane) on the `default.qubit` state-vector simulator with angle embedding in $[0, \pi]$ across 8 qubits, strongly entangling layers, and classical readout.

All three model families are evaluated under strict experimental discipline:
- **Target Label:** `risk_label` with two classes:
  - `Normal`: HbA1c (`LBXGH`) < 5.7%
  - `Elevated Risk` (Positive Class): 5.7% &le; HbA1c < 6.5% (Pre-diabetes range). Records with HbA1c &ge; 6.5% are excluded.
- **Shared Feature Set:** Exactly 5 raw predictors selected deterministically on training data only via mutual information, yielding 8 transformed feature columns.
- **Held-Out Test Set:** Natural prevalence ($n = 678$, prevalence $= 0.347$, unweighted).
- **Threshold Protocol:** Decision thresholds are selected on **validation data only** (maximizing sensitivity subject to validation specificity &ge; 0.70) and applied once to the test set.

---

## 2. Key Capabilities

- **Strict Data Pipeline & Leakage Prevention:** All scalers, imputers, and mutual information selectors are fit strictly on training splits (70/15/15 split hash: `04b66b2685790a6e...`).
- **Unified Model Strategy Pattern:** Standardized `ModelAdapter` interface allows interchangeable model execution, stubbing, and isolated failure recovery.
- **Responsive Single-Page Interface:** Vanilla JS single-page application adhering to an accessible grayscale-first design system with light/dark theme persistence and zero page reloads.
- **Automated MLOps Tracking:** Automated experiment logging with MLflow 3.x capturing parameters, metrics, confusion matrices, ROC coordinates, circuit diagrams, and serialized model artifacts.
- **Continuous Integration Pipeline:** 5-stage GitHub Actions CI workflow executing syntax validation, backend import resolution, 22 acceptance tests, MLflow integration tests, and application smoke tests.
- **Privacy & Security Safeguards:** Rejection of participant identifier columns (e.g., `SEQN`), sanitized CSV export defense against formula injection, and localhost-only network binding.

---

## 3. Architecture Overview

The system follows a modular, layered architecture designed for local execution and strict reproducibility:

- **Presentation Layer (`frontend/`):** Semantic HTML5 shell, CSS3 stylesheet implementing a strict grayscale palette, and modular client-side routing with hash navigation.
- **API & Routing Layer (`backend/api/`):** FastAPI application providing REST endpoints for dataset statistics, model benchmark execution, results comparison, and tracking status.
- **Orchestration Layer (`backend/orchestration/`):** Asynchronous benchmark execution engine with thread-safe progress tracking and fault isolation across model families.
- **Model Adapter Layer (`backend/models/`):** Unified `ModelAdapter` base class implemented by `MLAdapter`, `DLAdapter`, `QMLAdapter`, and `StubAdapter`.
- **Data & Preprocessing (`backend/data/`):** File validation, schema verification, missingness analysis, and serialized preprocessing transformer pipelines.
- **Evaluation & Reporting (`backend/evaluation/`, `backend/reports/`):** Metrics computation (accuracy, balanced accuracy, sensitivity, specificity, PPV, NPV, F1, AUC-ROC), bootstrap confidence intervals, and sanitized CSV/JSON report generators.
- **Tracking Layer (`backend/tracking/`):** Hierarchical experiment tracker managing parent benchmark runs and child model runs in MLflow.

---

## 4. Technology Stack

- **Backend Framework:** FastAPI 0.115+, Uvicorn, Pydantic, Starlette
- **Machine Learning & Scientific Libraries:** Scikit-learn 1.5+, PyTorch 2.5+ (CPU), PennyLane 0.39+, NumPy, Pandas, Joblib
- **Experiment Tracking & CI/CD:** MLflow 3.x, GitHub Actions
- **Frontend:** Vanilla JavaScript (ES6+), CSS3 (Grayscale Design System), HTML5
- **Testing & Quality Assurance:** Pytest 9.x, Selenium, Google Chrome Headless
- **Survey Dataset:** CDC National Health and Nutrition Examination Survey (NHANES) 2017–2018 Cycle

---

## 5. Prerequisites

- **Operating System:** Windows 10/11, macOS, or Linux (x86_64)
- **Python:** Python 3.11 or 3.12 (standard 64-bit distribution)
- **Git:** Git 2.30 or newer
- **Browser:** Modern web browser (Google Chrome, Mozilla Firefox, or Microsoft Edge)

---

## 6. Installation and Setup

### Step 1: Clone the Repository
```powershell
git clone https://github.com/PES1UG24AM004/SE-Mini-Project.git
cd SE-Mini-Project
```

### Step 2: Set Up Virtual Environment & Dependencies
```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Upgrade pip and install pinned dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
```powershell
Copy-Item .env.example .env
```

---

## 7. How to Run the Application

### Start the Application Server
```powershell
python run_server.py
```
Open your browser and navigate to:
```
http://127.0.0.1:8000
```

### (Optional) Start Local MLflow Tracking Server
To enable live experiment tracking with the MLflow graphical user interface:
```powershell
# In a separate PowerShell terminal:
.\scripts\start_mlflow.ps1
```
Open the MLflow dashboard at:
```
http://127.0.0.1:5000
```

---

## 8. How to Execute Tests

### 1. Run Automated Test Suite (All 37 Tests)
Executes the 22 Software Requirements Specification acceptance tests (`TC-01` through `TC-22`) and 15 MLflow integration tests:
```powershell
.\.venv\Scripts\pytest -v tests
```

### 2. Run UI & Responsive Viewport Verification
```powershell
# 25-Point Google Chrome regression checklist (saves screenshots to artifacts/browser-tests/):
.\.venv\Scripts\python scripts/test_chrome_regression_checklist.py

# Multi-viewport responsiveness verification (1440px, 1024px, 768px, 390px, 360px):
.\.venv\Scripts\python scripts/check_viewports.py
```

---

## 9. Documentation Index

Comprehensive academic and engineering documentation is maintained in the [`docs/`](docs/) directory:

| Section | Key Deliverable | Format | Purpose |
| :--- | :--- | :--- | :--- |
| [**Central Index**](docs/README.md) | [`docs/README.md`](docs/README.md) | Markdown | Complete documentation roadmap and status catalog. |
| [**01-Requirements**](docs/01-requirements/) | [`product-backlog.docx`](docs/01-requirements/product-backlog.docx) | DOCX | 63-item Jira backlog mapped to SRS requirements (AE2). |
| | [`software-requirements-specification.pdf`](docs/01-requirements/software-requirements-specification.pdf) | PDF | Authoritative 31-page course specification (Part 1). |
| | [`requirements-traceability-matrix.md`](docs/01-requirements/requirements-traceability-matrix.md) | Markdown | Bidirectional RTM mapping requirements to code and tests. |
| [**02-Architecture**](docs/02-architecture/) | [`software-architecture-and-design.docx`](docs/02-architecture/software-architecture-and-design.docx) | DOCX | Layered architecture, model adapters, and security design (Part B). |
| [**03-Sprints**](docs/03-sprints/) | [`sprint-1-reconstructed.docx`](docs/03-sprints/sprint-1-reconstructed.docx) | DOCX | Reconstructed Sprint 1 planning and candidate scope. |
| | [`sprint-2-interim.docx`](docs/03-sprints/sprint-2-interim.docx) | DOCX | Sprint 2 interim scope, burnup, and review. |
| [**04-Testing**](docs/04-testing/) | [`software-test-plan.docx`](docs/04-testing/software-test-plan.docx) | DOCX | IEEE-style test plan defining TC-01 to TC-22 (Part C). |
| | [`unit-test-report.docx`](docs/04-testing/unit-test-report.docx) | DOCX | Unit and component test report (AE4 draft). |
| | [`system-test-report.docx`](docs/04-testing/system-test-report.docx) | DOCX | System-level integration test report with illustrative mock formats. |
| [**05-DevOps**](docs/05-devops/) | [`devops-tool-adoption.docx`](docs/05-devops/devops-tool-adoption.docx) | DOCX | DevOps tool adoption record distinguishing evidence from plans (AE5). |
| | [`mlops-guide.md`](docs/05-devops/mlops-guide.md) | Markdown | Engineering guide for GitHub Actions CI and MLflow tracking. |
| [**Reports**](docs/reports/) | [`documentation-consolidation-report.md`](docs/reports/documentation-consolidation-report.md) | Markdown | Final audit report of repository consolidation and verification. |
| | [`codecraft-complete-project-audit.md`](docs/reports/codecraft-complete-project-audit.md) | Markdown | Deep technical project audit and leakage verification. |
| | [`automated-test-execution-report.md`](docs/reports/automated-test-execution-report.md) | Markdown | Historical test execution record for TC-01 through TC-22. |

---

## 10. Repository Structure

```
.
├── .github/workflows/ci.yml       # GitHub Actions automated continuous integration
├── .env.example                   # Environment configuration template
├── .gitignore                     # Git hygiene and ignore rules
├── README.md                      # Primary project overview, setup, and navigation
├── requirements.txt               # Pinned Python package dependencies
├── run_server.py                  # Single-command application entry point
├── artifacts/                     # UI test screenshots and responsive previews
│   ├── browser-tests/             # Automated Chrome 25-point test verification
│   ├── responsive-previews/       # Multi-viewport responsive snapshots
│   └── ui-checks/                 # Light/Dark theme and navigation checks
├── backend/                       # Layered FastAPI backend application
│   ├── api/                       # REST endpoints and route handlers
│   ├── config.py                  # Global application constants and paths
│   ├── data/                      # Validators, preprocessors, and schemas
│   ├── evaluation/                # Metrics calculation and threshold optimizer
│   ├── models/                    # Model adapters (ML, DL, QML, Stub)
│   ├── orchestration/             # Benchmark orchestrator and fault isolation
│   ├── reports/                   # CSV/JSON report generators
│   ├── storage/                   # Atomic results store and reference data
│   └── tracking/                  # MLflow experiment tracking adapter
├── data/                          # Survey data artifacts and split manifests
│   ├── processed/                 # Model-ready and merged adult cohorts
│   ├── reports/                   # Data exploration and audit reports
│   └── splits/                    # Deterministic 70/15/15 train/val/test splits
├── docs/                          # Consolidated academic and technical documentation
│   ├── README.md                  # Central documentation index and status guide
│   ├── 01-requirements/           # Backlog, baseline SRS PDF, and RTM
│   ├── 02-architecture/           # Software Architecture and Design (SAD)
│   ├── 03-sprints/                # Sprint 1 (reconstructed) & Sprint 2 (interim)
│   ├── 04-testing/                # STP, Unit Test Report, System Test Report
│   ├── 05-devops/                 # DevOps adoption report & MLOps guide
│   ├── reports/                   # Technical audits and consolidation reports
│   └── archive/                   # Deprecated or historical documentation
├── frontend/                      # Vanilla JavaScript single-page application
│   ├── static/                    # Stylesheet (grayscale palette) and client app
│   └── templates/                 # Accessible HTML5 application shell
├── models/preprocessing/          # Serialized scikit-learn transformers
├── notebooks/                     # Exploratory research and model training notebooks
├── raw/                           # Raw NHANES 2017–2018 SAS transport files
├── results/                       # Baseline references and benchmark run records
│   ├── reference_results.json     # Verified benchmark reference metrics
│   ├── shared_feature_set.json    # Canonical 5-feature metadata
│   └── runs/                      # Benchmark execution run logs
├── scripts/                       # Local execution, verification, and MLOps scripts
└── tests/                         # Pytest test suite (TC-01..22 and MLOps)
```

---

## 11. Benchmark Reference Results

Evaluated on held-out NHANES 2017–2018 test records ($n = 678$, unweighted prevalence $= 0.347$) with decision thresholds selected on validation data only (sensitivity @ specificity &ge; 0.70):

| Model Family | Paradigm | Test Accuracy | Balanced Acc | Sensitivity | Specificity | AUC-ROC | Inference Latency |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Classical ML** | `HistGradientBoosting` | **0.7817** | **0.7766** | **0.7617** | **0.7923** | **0.8654** | < 1 ms |
| **Deep Learning** | PyTorch MLP | 0.7655 &plusmn; 0.007 | 0.7588 &plusmn; 0.008 | 0.7362 &plusmn; 0.021 | 0.7810 &plusmn; 0.014 | 0.8492 &plusmn; 0.006 | ~ 2 ms |
| **Quantum ML** | PennyLane VQC (8-qubit) | 0.7242 &plusmn; 0.012 | 0.7185 &plusmn; 0.011 | 0.7021 &plusmn; 0.019 | 0.7359 &plusmn; 0.015 | 0.7915 &plusmn; 0.009 | ~ 85 ms |

---

## 12. Non-Diagnostic Limitation & Ethical Disclosure

1. **Cross-Sectional Limitation:** The NHANES dataset measures participant biomarkers at a single cross-sectional point in time. The predictions reflect association with elevated HbA1c ($5.7\% \le \text{HbA1c} < 6.5\%$) during survey examination, not a longitudinal prognosis or clinical diabetes diagnosis.
2. **Unweighted Sample Evaluation:** Models were trained and evaluated on raw sample records without applying NHANES complex survey strata or examination sample weights.
3. **Simulated Quantum Execution:** The Quantum Machine Learning model was trained and evaluated on classical CPU state-vector simulation (`default.qubit`). No physical quantum hardware was utilized.

---

## 13. Team & Attribution

**Team Name:** CodeCraft  
**Course:** Software Engineering Mini-Project  
**Institution:** PES University (RR Campus)  

**Team Members:**
- **Aarav Yuval B G** — SRN: `PES1UG24AM004` (Lead Engineer / Integration)
- **Abhay TS** — SRN: `PES1UG24AM008`
- **Abhishek PH** — SRN: `PES1UG24AM013`
