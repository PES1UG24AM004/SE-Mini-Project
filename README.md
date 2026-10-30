# CodeCraft — Early Metabolic Risk Detection Website
### Benchmark Comparison of Classical ML vs Deep Learning vs Quantum ML on NHANES 2017–2018

> **Academic Research & Educational Use Disclaimer:**  
> **Research/educational use only. Not a diagnosis or medical advice.**  
> This platform implements a cross-sectional classification benchmark within the NHANES 2017–2018 survey cycle. It does not predict future disease incidence or clinical onset.

---

## 1. Project Overview

The **CodeCraft Early Metabolic Risk Detection Platform** is a local-first, privacy-preserving research website built for the Software Engineering Mini-Project at PES University. The application benchmarks three distinct modeling paradigms on held-out records from the **NHANES 2017–2018** cycle:

1. **Classical Machine Learning (ML):** `HistGradientBoostingClassifier` (scikit-learn) with balanced sample weighting.
2. **Deep Learning (DL):** Feed-forward Multi-Layer Perceptron (PyTorch) with dropout, Adam optimizer, positive class loss weighting, and validation early stopping.
3. **Quantum Machine Learning (QML):** Variational Quantum Classifier (PennyLane) on the `default.qubit` state-vector simulator with angle embedding in $[0, \pi]$ across 8 qubits, strongly entangling layers, and classical readout.

All three model families are trained and evaluated under strict experimental discipline:
- **Target Label:** `risk_label` with two classes:
  - `Normal`: HbA1c (`LBXGH`) < 5.7%
  - `Elevated Risk` (Positive Class): 5.7% &le; HbA1c < 6.5% (Pre-diabetes range). Records with HbA1c &ge; 6.5% are excluded.
- **Shared Feature Set:** Exactly 5 raw predictors selected deterministically on training data only via mutual information, yielding 8 transformed feature columns.
- **Held-Out Test Set:** Natural prevalence ($n = 678$, prevalence $= 0.347$, unweighted).
- **Threshold Protocol:** Decision thresholds are selected on **validation data only** (maximizing sensitivity subject to validation specificity &ge; 0.70) and applied once to the test set.

---

## 2. System Architecture

The application adopts a clean, layered architecture with modular separation of concerns:

```
├── CODECRAFT_COMPLETE_PROJECT_AUDIT.md # Technical audit report & architecture verification
├── CodeCraft_Early_Metabolic_Risk_Specification (1).pdf # 31-page SRS & test specification
├── README.md            # Setup guide, architecture, benchmark results, walkthrough
├── requirements.txt     # Pinned Python package dependencies
├── run_server.py        # Single-command startup entry point (127.0.0.1:8000)
├── .env.example         # Template for environment configuration
├── artifacts/           # Browser test verification, responsive previews & UI checks
│   ├── browser-tests/   # Automated Chrome test verification screenshots
│   ├── responsive-previews/ # Multi-viewport layout previews (mobile, tablet, desktop)
│   └── ui-checks/       # Light/Dark theme and navigation check captures
├── backend/             # FastAPI backend with layered architecture
│   ├── api/             # REST endpoints, CORS, static file mounts
│   ├── config.py        # Project constants, paths, seed definitions
│   ├── data/            # Preprocessor, validators, schema checks
│   ├── evaluation/      # Metric calculations, threshold selection, bootstrap CI
│   ├── models/          # Adapters: Classical ML, PyTorch DL, PennyLane QML, Stub
│   ├── orchestration/   # Asynchronous execution, progress tracking & fault isolation
│   ├── reports/         # Aggregate JSON, CSV (formula sanitized), HTML report generator
│   └── storage/         # Atomic results store & baseline reference repository
├── data/                # CDC NHANES 2017-2018 datasets & reports
│   ├── processed/       # Merged adult cohorts & model-ready CSVs
│   ├── reports/         # Dataset audit reports, dictionaries, splitting logs
│   └── splits/          # Fixed 70/15/15 train, validation, and test splits
├── docs/                # Project documentation, traceability matrix & test reports
│   ├── browser-debug-report.md # Chrome DevTools debug report and root causes
│   ├── frontend-repair-notes.md # Responsive & theme implementation notes
│   ├── requirements-traceability.md # RTM mapping SRS to code & tests
│   └── test-plan.md     # Full Software Test Plan & executed results (TC-01 to TC-22)
├── frontend/            # Vanilla JS SPA with responsive scientific interface
│   ├── static/          # CSS stylesheet (grayscale design system) and JS client
│   └── templates/       # HTML5 single-page application shell
├── models/              # Preprocessing pipelines & joblib transformers
│   └── preprocessing/   # Serialized preprocessors
├── notebooks/           # Jupyter research notebooks (ML, DL, QML pipelines)
│   ├── 01_dataset_loading_and_preparation.ipynb
│   ├── 02_ml_model.ipynb
│   ├── 03_dl_model.ipynb
│   ├── 04_qml_model.ipynb
│   ├── DL_model.ipynb
│   ├── ML_model.ipynb
│   └── QML_model.ipynb
├── raw/                 # NHANES raw survey files (BMX_J.XPT, DEMO_J.XPT, GHB_J.XPT)
├── results/             # Benchmark run records, shared feature set & reference results
│   ├── reference_results.json # Verified notebook baseline reference metrics
│   ├── shared_feature_set.json # Canonical 5-feature metadata & MI rankings
│   └── runs/            # Historical benchmark execution records
├── scripts/             # End-to-end browser regression & viewport verification scripts
│   ├── check_viewports.py # Multi-viewport responsiveness verification
│   └── test_chrome_regression_checklist.py # 25-point Chrome regression test script
└── tests/               # Automated test suite (TC-01 through TC-22 acceptance tests)
    └── test_all_requirements.py
```

---

## 3. Environment Setup & Launch

### Prerequisites
- Python 3.11 or 3.12 installed on Windows, macOS, or Linux.
- Modern web browser (Chrome, Edge, Firefox).

### Step 1: Clone or Navigate to the Workspace
```powershell
git clone https://github.com/PES1UG24AM004/SE-Mini-Project.git
cd SE-Mini-Project
```
Or if working in the local academic directory:
```powershell
cd C:\Users\Aarav\Documents\Studies\Sem5\Assignments\Software_Engineering\MIni
```

### Step 2: Set Up Virtual Environment & Dependencies
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Step 3: Start the Local Server (Single Command)
```powershell
python run_server.py
```
The server binds exclusively to `127.0.0.1:8000` (localhost only).  
Open your browser and navigate to:
```
http://127.0.0.1:8000
```

---

## 4. User Walkthrough (15-Minute First-Time Flow)

The user interface features a single-page application (SPA) architecture with hash-based routing (`window.location.hash`), instant tab switching, browser Back/Forward history support, and a strict grayscale Light/Dark theme toggle persisting across sessions in `localStorage`:

1. **Overview (`/#overview`):**  
   Review the research purpose, NHANES 2017–2018 cycle context, summary cards, and non-diagnostic educational warning.
2. **Dataset (`/#dataset`):**  
   Inspect the cohort split counts (Train: 3,160; Val: 677; Test: 678), column schema, class balance, and the 5 selected predictors (`RIDAGEYR`, `DMDHRAGZ`, `DMDHHSZE`, `BMXWAIST`, `BMXBMI`). Click **Run Validation** to verify schema and data hygiene in real time.
3. **Run Models (`/#run`):**  
   Select which model families to train (`ML`, `DL`, `QML`), configure the random seed (default `42`), and choose single-seed or 5-seed repeats. Click **Launch Selected Models**. Execution acknowledges within 2 seconds with live progress tracking, elapsed time, and peak memory logging.
4. **Comparison (`/#comparison` - Primary View):**  
   Inspect the head-to-head aligned comparison table. Switch between the **Imported Notebook Reference** and fresh local runs. View side-by-side metrics:
   - **Primary Metric:** Sensitivity @ validation-chosen threshold (target specificity &ge; 0.70).
   - Test Specificity, Precision, F1, Accuracy, ROC-AUC, Threshold, and Confusion Matrix.
   - Interactive SVG Bar Charts and ROC Curves with non-color cues (solid `●` for ML, dashed `■` for DL, dotted `◆` for QML) for grayscale clarity.
5. **Model Details (`/#details`):**  
   Click any model family to inspect its algorithm details, hyperparameters, library versions, compute backend, and known limitations. For QML, view the rendered 8-qubit variational circuit diagram.
6. **Single Record (`/#predict`):**  
   Enter patient predictor values into the interactive form. The system executes client-side and server-side validation, generates positive-class probability, compares against the decision threshold, and presents the estimate alongside the non-diagnostic warning banner.
7. **Export (`/#export`):**  
   Download aggregate-only research reports in **JSON**, **CSV** (with spreadsheet formula injection protection), or **Printable HTML**. No participant-level rows or raw predictions are ever exported.

---

## 5. Model Protocol & Notebook Baseline Reference

The system pre-loads the verified baseline reference results directly derived from the executed Colab notebooks (`ML_model.ipynb`, `DL_model.ipynb`, `QML_model.ipynb`):

| Property / Metric | Classical ML (HistGB) | Deep Learning (MLP) | Quantum ML (PennyLane VQC) |
| :--- | :--- | :--- | :--- |
| **Model Algorithm** | `HistGradientBoosting` | PyTorch Feed-Forward MLP | Variational Quantum Circuit |
| **Execution Backend** | CPU | CPU (PyTorch) | PennyLane `default.qubit` (CPU Simulator) |
| **Seeds Evaluated** | 42 | 42–46 (5 seeds) | 42–46 (5 seeds) |
| **Headline Reporting** | Seed 42 with 95% Bootstrap CI | Mean &plusmn; SD across 5 seeds | Mean &plusmn; SD across 5 seeds |
| **Sensitivity (Primary)** | **0.677** [0.620, 0.739] | **0.661 &plusmn; 0.010** | **0.647 &plusmn; 0.040** |
| **Specificity** | 0.729 [0.686, 0.769] | 0.719 &plusmn; 0.005 | 0.702 &plusmn; 0.013 |
| **Precision** | 0.570 [0.511, 0.629] | 0.555 &plusmn; 0.002 | 0.535 &plusmn; 0.008 |
| **F1 Score** | 0.619 [0.570, 0.668] | 0.604 &plusmn; 0.004 | 0.585 &plusmn; 0.020 |
| **Accuracy** | 0.711 [0.678, 0.743] | 0.699 &plusmn; 0.001 | 0.683 &plusmn; 0.007 |
| **ROC-AUC** | 0.759 [0.725, 0.796] | 0.768 &plusmn; 0.002 | 0.732 &plusmn; 0.014 |
| **Decision Threshold** | 0.5897 | 0.583 &plusmn; 0.004 | 0.557 &plusmn; 0.030 |
| **Confusion Matrix** | `[[323, 120], [76, 159]]` | Available on fresh run | Available on fresh run |
| **Runtime** | 46.52 s | 4.65 s | 32.12 s |
| **Peak Memory** | 326.6 MB | 340.2 MB | 355.8 MB |

*Note on Seed Variation:* Standard deviation (SD) for DL and QML reflects variation across different random weight initializations on the single fixed test split. It is not a confidence interval for generalization to new populations.

---

## 6. Verification & Automated Testing

The repository contains an automated test suite verifying all 22 Software Requirements Specification test cases (`TC-01` through `TC-22`):

```powershell
.\.venv\Scripts\pytest -v tests
```

Additionally, end-to-end browser and UI responsiveness tests can be executed via Selenium:
```powershell
# 25-Point Google Chrome regression checklist (saves screenshots to artifacts/browser-tests/):
.\.venv\Scripts\python scripts/test_chrome_regression_checklist.py

# Multi-viewport responsiveness verification (1440px, 1024px, 768px, 390px, 360px):
.\.venv\Scripts\python scripts/check_viewports.py
```
This verifies 0 console errors, tab switching, direct bookmark loading, browser history back/forward navigation, theme toggle persistence, and exports screenshots to `artifacts/browser-tests/` and `artifacts/responsive-previews/`.

### Verified Test Cases Summary:
- **TC-01 to TC-03:** Valid import, missing target rejection, invalid type/range/single-class error logging.
- **TC-04 to TC-05:** Shared split hash verification, leakage prevention (train-only transforms), separate model run logging.
- **TC-06:** Metric computation accuracy to 4 decimal places and undefined metric (`n/a`) handling.
- **TC-07 to TC-08:** Side-by-side comparison surface and prediction safety validation.
- **TC-09:** Privacy enforcement (identifier columns like `SEQN` rejected; aggregate-only exports).
- **TC-10 to TC-12:** Provenance logging, workflow execution, dashboard model details, and report downloads.
- **TC-13:** Validation performance: **50,000 synthetic records validated in 0.182 seconds** (&le; 10s requirement).
- **TC-14:** Fault isolation: simulated model failure leaves sibling models and prior completed runs intact.
- **TC-15 to TC-17:** Usability checklist, pluggable `StubAdapter` maintainability, clean environment setup.
- **TC-18 to TC-19:** Accessibility (contrast &ge; 4.5:1, tabular numbers) and browser compatibility (Chrome at 1366&times;768 without horizontal overflow).
- **TC-20 to TC-22:** Disguised executable upload rejection, CSV formula injection protection, localhost-only binding, and memory limit handling.

---

## 7. Known Methodological Limitations

1. **Cross-Sectional Data:** NHANES surveys participants at a single snapshot in time. Elevated risk indicates concurrent biomarker patterns, not an epidemiological forecast of future diabetes incidence.
2. **Unweighted Analysis:** The models are evaluated on unweighted sample data; they do not incorporate NHANES complex survey strata or sampling weights.
3. **Quantum Simulator Execution:** The QML pipeline executes on a classical CPU simulator (`default.qubit`). No quantum hardware was used, and no quantum supremacy/advantage is claimed.

---

## 8. Team & Attribution

**Team Name:** CodeCraft  
**Course:** Software Engineering Mini-Project  
**Instructor:** Cvsn Reddy  
**University:** PES University (RR Campus)  

**Team Members:**
- **Aarav Yuval B G** — SRN: `PES1UG24AM004`
- **Abhay TS** — SRN: `PES1UG24AM008`
- **Abhishek PH** — SRN: `PES1UG24AM013`
