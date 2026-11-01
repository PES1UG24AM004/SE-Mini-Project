# CodeCraft
**Early Metabolic Risk Detection — Classical ML vs Deep Learning vs Quantum ML**

[![CodeCraft Continuous Integration](https://github.com/PES1UG24AM004/SE-Mini-Project/actions/workflows/ci.yml/badge.svg)](https://github.com/PES1UG24AM004/SE-Mini-Project/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MLflow 3.x](https://img.shields.io/badge/MLflow-3.x-0194E2.svg)](https://mlflow.org/)
[![License: Academic Research](https://img.shields.io/badge/License-Academic_Research-lightgrey.svg)](README.md)

An academic software engineering project developed at PES University that compares classical machine learning, deep learning, and quantum machine learning approaches on NHANES 2017–2018 data.

> **Disclaimer:** Educational research only. Not intended for clinical diagnosis or medical advice. Cross-sectional survey data reflects concurrent biomarker patterns, not an epidemiological forecast of future diabetes incidence.

---

### Quick Start

```powershell
# 1. Clone repository
git clone https://github.com/PES1UG24AM004/SE-Mini-Project.git
cd SE-Mini-Project

# 2. Set up virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install dependencies & configure environment
pip install -r requirements.txt
Copy-Item .env.example .env

# 4. Start local application server
python run_server.py
```

Open your browser and navigate to:
```
http://127.0.0.1:8000
```

*(Optional) To enable live MLflow experiment tracking on `http://127.0.0.1:5000`:*
```powershell
.\scripts\start_mlflow.ps1
```

---

## 1. Key Capabilities

- **Three-Paradigm Modeling:** Evaluates Classical ML (`HistGradientBoosting`), Deep Learning (PyTorch MLP), and Quantum ML (PennyLane Variational Quantum Classifier on 8 qubits).
- **Leakage-Free Pipeline:** All imputers, scalers, and mutual-information feature selectors fit strictly on training splits (70/15/15 stratified split, hash `04b66b2685790a6e`).
- **Validation-Driven Thresholds:** Decision thresholds tuned on validation data only (maximizing sensitivity subject to specificity &ge; 0.70) and evaluated once on the test set.
- **Single-Page Application:** Vanilla JavaScript frontend with an accessible grayscale design system, client-side routing, and zero page reloads.
- **Automated MLOps Tracking:** Automated logging of hyperparameters, evaluation metrics, ROC curves, and serialized artifacts with MLflow 3.x and GitHub Actions CI.
- **Privacy & Security Safeguards:** Disallows participant identifiers (e.g., `SEQN`), defenses against CSV formula injection, and binds strictly to localhost.

---

## 2. Technology Stack

- **Backend:** FastAPI, Uvicorn, Starlette, Pydantic, Python 3.11+
- **Machine Learning:** Scikit-learn, PyTorch (CPU), PennyLane, Joblib, NumPy, Pandas
- **Experiment Tracking & CI/CD:** MLflow 3.x, GitHub Actions
- **Frontend:** Vanilla JavaScript (ES6+), CSS3 (Grayscale Design System), HTML5
- **Quality Assurance:** Pytest, Selenium, Google Chrome Headless
- **Data Source:** CDC NHANES 2017–2018 Survey Cycle (Demographics, Examination, Laboratory)

---

## 3. High-Level Architecture

The platform uses a layered local architecture with interchangeable model adapters behind a unified interface:

```
[ Web Browser (Vanilla JS SPA) ]
               │
               ▼  REST API (localhost:8000)
    [ FastAPI Routing Layer ]
               │
    ┌──────────┴─────────────────────────┐
    ▼                                    ▼
[ Data Validation & Pipeline ]   [ Orchestration Engine ]
  • Schema & missingness check     • Threaded async runs
  • Train-only transformers        • Fault isolation
  • 5 canonical predictors         • Results persistence
                                         │
                 ┌───────────────────────┼───────────────────────┐
                 ▼                       ▼                       ▼
          [ ML Adapter ]          [ DL Adapter ]          [ QML Adapter ]
         (HistGradBoost)           (PyTorch MLP)          (PennyLane VQC)
                 │                       │                       │
                 └───────────────────────┼───────────────────────┘
                                         ▼
                             [ Evaluation & Tracking ]
                               • Held-out test metrics
                               • MLflow 3.x logging
```

---

## 4. Testing & Verification

Run the full automated test suite (22 SRS requirements tests + 15 MLflow integration tests):
```powershell
.\.venv\Scripts\pytest -v tests
```

Run UI regression and responsive viewport checks:
```powershell
# 25-point Google Chrome headless regression checklist:
python scripts/test_chrome_regression_checklist.py

# Multi-viewport responsive layout verification (desktop, tablet, mobile):
python scripts/check_viewports.py
```

---

## 5. Academic Documentation (30-Mark Rubric)

All coursework deliverables are organized in the [`docs/`](docs/) directory according to the 30-mark assessment rubric:

| Graded Deliverable | Marks | Canonical Path | Description |
| :--- | :---: | :--- | :--- |
| **Software Requirements Specification (SRS)** | 5 | [`docs/01-requirements/software-requirements-specification.pdf`](docs/01-requirements/software-requirements-specification.pdf) | Formal 31-page course specification (Part 1). |
| **Software Test Plan (STP)** | 2 | [`docs/04-testing/software-test-plan.docx`](docs/04-testing/software-test-plan.docx) | Formal IEEE-style test plan (TC-01 through TC-22). |
| **Software Architecture and Design (SAD)** | 3 | [`docs/02-architecture/software-architecture-and-design.docx`](docs/02-architecture/software-architecture-and-design.docx) | Layered architecture, adapters, and data flows. |
| **Product Backlog** | 4 | [`docs/01-requirements/product-backlog.docx`](docs/01-requirements/product-backlog.docx) | 13 epics, 63 work items mapped to SRS requirements. |
| **Sprint 1** | 3 | [`docs/03-sprints/sprint-1-reconstructed.docx`](docs/03-sprints/sprint-1-reconstructed.docx) | Reconstructed Sprint 1 planning and candidate scope. |
| **Sprint 2** | 3 | [`docs/03-sprints/sprint-2-interim.docx`](docs/03-sprints/sprint-2-interim.docx) | Sprint 2 interim scope, burnup, and review. |
| **Unit Test Report** | 4 | [`docs/04-testing/unit-test-report.docx`](docs/04-testing/unit-test-report.docx) | Unit & component test report (draft format). |
| **System Test Report** | 3 | [`docs/04-testing/system-test-report.docx`](docs/04-testing/system-test-report.docx) | System test report with illustrative mock formats. |
| **DevOps Tool Adoption** | 3 | [`docs/05-devops/devops-tool-adoption.docx`](docs/05-devops/devops-tool-adoption.docx) | Evidenced vs. reported DevOps adoption. |
| **TOTAL** | **30** | Complete catalog in [`docs/README.md`](docs/README.md) | Central documentation roadmap and statuses. |

*Additional supporting technical guides are located in [`docs/technical/`](docs/technical/) ([MLOps Guide](docs/technical/mlops-guide.md), [Traceability Matrix](docs/technical/requirements-traceability-matrix.md)).*

---

## 6. Benchmark Reference Results

Evaluated on held-out NHANES 2017–2018 test records ($n = 678$, unweighted prevalence $= 0.347$) with decision thresholds selected on validation data only (sensitivity @ specificity &ge; 0.70):

| Model Family | Paradigm | Test Accuracy | Balanced Acc | Sensitivity | Specificity | AUC-ROC | Latency |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Classical ML** | `HistGradientBoosting` | **0.7817** | **0.7766** | **0.7617** | **0.7923** | **0.8654** | < 1 ms |
| **Deep Learning** | PyTorch MLP | 0.7655 &plusmn; 0.007 | 0.7588 &plusmn; 0.008 | 0.7362 &plusmn; 0.021 | 0.7810 &plusmn; 0.014 | 0.8492 &plusmn; 0.006 | ~ 2 ms |
| **Quantum ML** | PennyLane VQC (8-qubit) | 0.7242 &plusmn; 0.012 | 0.7185 &plusmn; 0.011 | 0.7021 &plusmn; 0.019 | 0.7359 &plusmn; 0.015 | 0.7915 &plusmn; 0.009 | ~ 85 ms |

---

## 7. Team & Attribution

**Team Name:** CodeCraft  
**Course:** Software Engineering Mini-Project  
**Institution:** PES University (RR Campus)  

**Team Members:**
- **Aarav Yuval B G** — SRN: `PES1UG24AM004` 
- **Abhay TS** — SRN: `PES1UG24AM008`
- **Abhishek PH** — SRN: `PES1UG24AM013`
