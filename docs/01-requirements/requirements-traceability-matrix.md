# Requirements Traceability Matrix (RTM)

**Project:** CodeCraft Early Metabolic Risk Detection Website  
**Team Members:** Aarav Yuval (PES1UG24AM004), Abhay TS (PES1UG24AM008), Abhishek PH (PES1UG24AM013)  
**Institution:** PES University (RR Campus)  
**Course:** Software Engineering Mini-Project  
**Document Version:** 1.0.0 (October 2026)  

---

## 1. Functional Requirements (FR) Traceability

| Requirement ID | Description Summary | Implementation File(s) | Verified by Test Case(s) | Status |
| :--- | :--- | :--- | :--- | :--- |
| **FR-01** | Import prepared NHANES CSV (&le;50 MB) and display row/column counts | `backend/data/validator.py`<br>`backend/api/app.py` | `TC-01` | **PASSED** |
| **FR-02** | Validate schema, types, ranges, missingness, and target classes before training | `backend/data/validator.py` | `TC-02`, `TC-03` | **PASSED** |
| **FR-03** | Block training on validation failure with itemized field-level error messages | `backend/data/validator.py`<br>`backend/api/app.py` | `TC-02`, `TC-03` | **PASSED** |
| **FR-04** | Use reproducible stratified split (70/15/15) with identical row indices for ML, DL, QML | `backend/data/preprocessor.py` | `TC-04` | **PASSED** |
| **FR-05** | Fit imputers, scalers, encoders, and feature selection on training rows only | `backend/data/preprocessor.py`<br>`backend/models/` | `TC-04` | **PASSED** |
| **FR-06** | Train ML, DL, QML separately and persist family, config, seed, backend, status | `backend/models/`<br>`backend/orchestration/orchestrator.py` | `TC-05` | **PASSED** |
| **FR-07** | Compute accuracy, precision, sensitivity, specificity, F1, ROC-AUC, confusion matrix | `backend/evaluation/evaluator.py` | `TC-06` | **PASSED** |
| **FR-08** | Side-by-side comparison on identical held-out test records with primary ranking metric | `frontend/templates/index.html`<br>`frontend/static/js/app.js` | `TC-07` | **PASSED** |
| **FR-09** | Validated single-record prediction with field error checking and non-diagnostic warning | `backend/orchestration/orchestrator.py`<br>`frontend/static/js/app.js` | `TC-08` | **PASSED** |
| **FR-10** | Export aggregate comparison reports with provenance and no participant-level records | `backend/reports/generator.py`<br>`backend/api/app.py` | `TC-10`, `TC-12` | **PASSED** |
| **FR-11** | Store random seeds and configurations for exact reproducibility | `backend/storage/store.py`<br>`backend/config.py` | `TC-10` | **PASSED** |
| **FR-12** | Reject or exclude participant identifier and survey design columns | `backend/config.py`<br>`backend/data/preprocessor.py` | `TC-09` | **PASSED** |
| **FR-13** | Overview page presenting goal, NHANES cycle, model families, and educational warning | `frontend/templates/index.html` | `TC-11` | **PASSED** |
| **FR-14** | Dataset inspection page showing row/class counts, schema, and validation feedback | `frontend/templates/index.html`<br>`frontend/static/js/app.js` | `TC-01`, `TC-11` | **PASSED** |
| **FR-15** | Run controls for separate or combined model training with visible progress and error isolation | `backend/orchestration/orchestrator.py`<br>`frontend/templates/index.html` | `TC-11`, `TC-14` | **PASSED** |
| **FR-16** | Comparison dashboard with side-by-side table, SVG charts, and confusion matrices | `frontend/templates/index.html`<br>`frontend/static/js/app.js` | `TC-07`, `TC-12` | **PASSED** |
| **FR-17** | Downloadable aggregate reports in JSON, CSV, and HTML formats | `backend/reports/generator.py` | `TC-12` | **PASSED** |
| **FR-18** | Model details page with hyperparameters, runtime, memory, diagram, and limitations | `frontend/templates/index.html`<br>`frontend/static/js/app.js` | `TC-12` | **PASSED** |

---

## 2. Interface Requirements Traceability

| Requirement ID | Category | Description Summary | Implementation File(s) | Verified by Test Case(s) | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **UI-01** | User Interface | Aligned model comparison, dataset version, and test split explicitly labeled | `frontend/templates/index.html`<br>`frontend/static/css/style.css` | `TC-07` | **PASSED** |
| **UI-02** | User Interface | Undefined/unavailable metrics serialize as null and display as `n/a` | `backend/evaluation/evaluator.py`<br>`frontend/static/js/app.js` | `TC-06`, `TC-07` | **PASSED** |
| **UI-03** | User Interface | Research/educational non-diagnostic warning banner on every result page | `frontend/templates/index.html`<br>`backend/config.py` | `TC-08` | **PASSED** |
| **UI-04** | User Interface | Accessible non-colour cues, patterns, markers, line styles, grayscale readability | `frontend/static/css/style.css`<br>`frontend/static/js/app.js` | `TC-18` | **PASSED** |
| **HW-01** | Hardware | Reports execution compute backend (CPU/GPU/Simulator) and resource logging | `backend/models/`<br>`backend/orchestration/orchestrator.py` | `TC-05` | **PASSED** |
| **SW-01** | Software | Rejects non-CSV or corrupted schemas with structured machine-readable error codes | `backend/data/validator.py`<br>`backend/api/app.py` | `TC-02`, `TC-20` | **PASSED** |
| **COM-01** | Communications | Localhost binding only (`127.0.0.1`), no third-party CDNs or external data transfers | `backend/config.py`<br>`run_server.py` | `TC-21` | **PASSED** |

---

## 3. Non-Functional Requirements (NFR) Traceability

| Requirement ID | Category | Specification | Implementation File(s) | Verified by Test Case(s) | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **NFR-01** | Performance | Validation time &le; 10s for 50,000 synthetic rows; training times recorded | `backend/data/validator.py`<br>`backend/orchestration/orchestrator.py` | `TC-13` | **PASSED** |
| **NFR-02** | Reliability | Fault isolation: failed model never halts others and leaves earlier runs intact | `backend/orchestration/orchestrator.py`<br>`backend/storage/store.py` | `TC-14` | **PASSED** |
| **NFR-03** | Reproducibility | Fixed seed splits; 5-seed repeats for DL/QML reported as mean &plusmn; SD | `backend/models/`<br>`backend/evaluation/evaluator.py` | `TC-10` | **PASSED** |
| **NFR-04** | Security/Privacy | Identifier exclusion; aggregate-only exports; no participant leakage | `backend/config.py`<br>`backend/reports/generator.py` | `TC-09`, `TC-21` | **PASSED** |
| **NFR-05** | Usability | Intuitive student flow (import &rarr; validate &rarr; run &rarr; compare &rarr; export) | `frontend/templates/index.html`<br>`README.md` | `TC-15` | **PASSED** |
| **NFR-06** | Maintainability | Pluggable `ModelAdapter` interface (`fit`, `predict_proba`, `describe`) | `backend/models/base.py`<br>`backend/models/stub_adapter.py` | `TC-16` | **PASSED** |
| **NFR-07** | Portability | Runs offline with pinned dependencies in one `requirements.txt` | `requirements.txt`<br>`run_server.py` | `TC-17` | **PASSED** |
| **NFR-08** | Readability | WCAG contrast &ge; 4.5:1, tabular numbers, visible focus, `prefers-reduced-motion` | `frontend/static/css/style.css` | `TC-18` | **PASSED** |
| **NFR-09** | Responsiveness | Run status acknowledgement &le; 2s; comparison dashboard render &le; 5s | `backend/api/app.py`<br>`frontend/static/js/app.js` | `TC-11`, `TC-19` | **PASSED** |
| **NFR-10** | Compatibility | Responsive layout at 1366&times;768 and mobile viewports with no horizontal scroll | `frontend/static/css/style.css` | `TC-19` | **PASSED** |
| **NFR-11** | Resource Logging | Process runtime and peak memory logged via `psutil`; graceful memory limits | `backend/orchestration/orchestrator.py` | `TC-22` | **PASSED** |

---

## 4. Security Requirements (SR) Traceability

| Requirement ID | Description Summary | Implementation File(s) | Verified by Test Case(s) | Status |
| :--- | :--- | :--- | :--- | :--- |
| **SR-1** | Approved de-identified data only; identity columns (`SEQN`, etc.) excluded | `backend/config.py`<br>`backend/data/preprocessor.py` | `TC-09` | **PASSED** |
| **SR-2** | Workspace-only storage; `.gitignore` verified to exclude `.venv` and secrets | `.gitignore`<br>`backend/config.py` | `TC-21` | **PASSED** |
| **SR-3** | Provenance metadata included in every exported report | `backend/reports/generator.py` | `TC-10` | **PASSED** |
| **SR-4** | External transfer disabled; localhost-only network traffic | `backend/config.py`<br>`backend/api/app.py` | `TC-21` | **PASSED** |
| **SR-5** | Upload safety: binary executables rejected, CSV formula injection escaped | `backend/data/validator.py` | `TC-20` | **PASSED** |
| **SR-6** | Localhost binding (`127.0.0.1:8000`); secrets excluded from source code | `backend/config.py`<br>`run_server.py` | `TC-21` | **PASSED** |
