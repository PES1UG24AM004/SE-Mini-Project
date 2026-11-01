# Software Test Plan & Execution Report

**Project:** CodeCraft Early Metabolic Risk Detection Website  
**Team Members:** Aarav Yuval (PES1UG24AM004), Abhay TS (PES1UG24AM008), Abhishek PH (PES1UG24AM013)  
**Institution:** PES University (RR Campus)  
**Execution Environment:** Windows 11, Python 3.12.10, PyTest 9.1.1, Google Chrome 155.0  
**Test Suite:** `tests/test_all_requirements.py`  
**Execution Timestamp:** 2026-10-24 03:01:58 UTC+05:30  
**Overall Outcome:** **22 Passed / 0 Failed (100% Pass Rate)**  

---

## 1. Test Execution Summary

The entire suite of 22 test cases specified in the CodeCraft Software Test Plan (Part C of the Specification) was automated and executed. Small deterministic fixtures were utilized where applicable to ensure rapid execution without sacrificing rigor.

```text
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Users\Aarav\Documents\Studies\Sem5\Assignments\Software_Engineering\MIni
collected 22 items

tests/test_all_requirements.py::test_tc01_valid_import PASSED            [  4%]
tests/test_all_requirements.py::test_tc02_missing_target PASSED          [  9%]
tests/test_all_requirements.py::test_tc03_invalid_values PASSED          [ 13%]
tests/test_all_requirements.py::test_tc04_shared_split_leakage PASSED    [ 18%]
tests/test_all_requirements.py::test_tc05_separate_model_training PASSED [ 22%]
tests/test_all_requirements.py::test_tc06_metric_correctness PASSED      [ 27%]
tests/test_all_requirements.py::test_tc07_comparison_display PASSED      [ 31%]
tests/test_all_requirements.py::test_tc08_prediction_safety PASSED       [ 36%]
tests/test_all_requirements.py::test_tc09_privacy_and_identifier_exclusion PASSED [ 40%]
tests/test_all_requirements.py::test_tc10_export_and_reproducibility PASSED [ 45%]
tests/test_all_requirements.py::test_tc11_run_workflow PASSED            [ 50%]
tests/test_all_requirements.py::test_tc12_dashboard_details_and_export PASSED [ 54%]
tests/test_all_requirements.py::test_tc13_validation_performance PASSED  [ 59%]
tests/test_all_requirements.py::test_tc14_failure_recovery_isolation PASSED [ 63%]
tests/test_all_requirements.py::test_tc15_usability_checklist PASSED     [ 68%]
tests/test_all_requirements.py::test_tc16_maintainability_stub_adapter PASSED [ 72%]
tests/test_all_requirements.py::test_tc17_portability PASSED             [ 77%]
tests/test_all_requirements.py::test_tc18_readability_accessibility PASSED [ 81%]
tests/test_all_requirements.py::test_tc19_browser_responsiveness PASSED  [ 86%]
tests/test_all_requirements.py::test_tc20_upload_safety_and_formulas PASSED [ 90%]
tests/test_all_requirements.py::test_tc21_network_secrets_gitignore PASSED [ 95%]
tests/test_all_requirements.py::test_tc22_resource_logging PASSED        [100%]

======================= 22 passed in 15.45s ========================
```

---

## 2. Test Execution Records (TC-01 through TC-22)

| Test ID | Test Name | Type | Traces To | Result | Evidence & Observed Metrics |
| :--- | :--- | :---: | :--- | :---: | :--- |
| **TC-01** | Valid Import | F | FR-01, FR-14 | **PASS** | 4,515 rows, 53 columns, 2 classes verified via `GET /api/dataset`. |
| **TC-02** | Missing Target | F | FR-02, FR-03 | **PASS** | Schema validator flagged missing `risk_label` and blocked execution with `missing_target` issue. |
| **TC-03** | Invalid Values & Missingness | F | FR-02, FR-03, NFR-02 | **PASS** | Itemized fields (`RIDAGEYR`, `BMXBMI`, `risk_label`) flagged with type/range/single-class errors. |
| **TC-04** | Shared Split / Leakage | F | FR-04, FR-05 | **PASS** | Split SHA-256 hash verified identical; train/val/test disjoint; transforms fit on train rows only. |
| **TC-05** | Separate Training | F | FR-06, HW-01, SW-01 | **PASS** | ML, DL, QML each produced distinct run records with family, config, seed, backend, status. |
| **TC-06** | Metric Correctness | F | FR-07 | **PASS** | Accuracy, precision, recall, specificity, F1, ROC-AUC matched independent calculation to 4 decimals; undefined cases return `None` (`n/a`). |
| **TC-07** | Comparison Display | F | FR-08, FR-16, UI-01, UI-02, UI-04 | **PASS** | Side-by-side comparison on identical test split (N=678, prevalence=0.347); primary ranking metric `sensitivity@spec>=0.70` displayed. |
| **TC-08** | Prediction Safety | F | FR-09, UI-03 | **PASS** | Valid input produced score 0.1245 and Normal class with warning banner; invalid input blocked with field errors. |
| **TC-09** | Privacy Checks | S | FR-12, NFR-04, SR-1, SR-4 | **PASS** | Columns `SEQN` and `participant_name` blocked with `privacy_violation`; aggregate exports contain zero participant rows. |
| **TC-10** | Export & Reproducibility | F | FR-10, FR-11, NFR-03, SR-3 | **PASS** | JSON/CSV/HTML exports include split hash, seed 42, library versions, timestamp, aggregate metrics. |
| **TC-11** | Website Run Workflow | F | FR-13, FR-14, FR-15, NFR-09 | **PASS** | Model launch acknowledged in 0.05s (&le;2s); status polling reflected queued &rarr; running &rarr; completed. |
| **TC-12** | Dashboard, Details & Export | F | FR-10, FR-16, FR-17, FR-18 | **PASS** | Dashboard displays side-by-side comparison, confusion matrices; details view provides full hyperparameter set; exports verified. |
| **TC-13** | Validation Performance | NF | NFR-01 | **PASS** | **50,000-row synthetic fixture validated in 0.182 seconds** (&le;10.0s requirement). |
| **TC-14** | Failure Recovery & Isolation | NF | NFR-02, FR-15 | **PASS** | Injected failure in DL model failed gracefully; ML model completed normally; previous baseline preserved intact. |
| **TC-15** | Usability Walkthrough | NF | NFR-05 | **PASS** | First-time student flow (Import &rarr; Validate &rarr; Run &rarr; Compare &rarr; Export) executed via UI and API without code editing. |
| **TC-16** | Maintainability | NF | NFR-06 | **PASS** | `StubAdapter` implementing `fit`, `predict_proba`, `describe` executed seamlessly with evaluator and test harness. |
| **TC-17** | Portability | NF | NFR-07 | **PASS** | Clean environment starts with one dependency file (`requirements.txt`); versions pinned and verified. |
| **TC-18** | Readability & Accessibility | NF | NFR-08 | **PASS** | WCAG contrast &ge; 4.5:1 verified; tabular numbers for metrics; non-color cues (symbols ●, ■, ◆; line styles; hatching); `prefers-reduced-motion` enabled. |
| **TC-19** | Browser Compatibility & Responsiveness | NF | NFR-09, NFR-10 | **PASS** | Headless Chrome verified at 1366&times;768 and mobile 375&times;667; zero horizontal overflow (`scrollWidth <= windowWidth`); status acknowledge &le;2s. |
| **TC-20** | Upload Safety & Formula Injection | S | SR-5 | **PASS** | Disguised executable header (`MZ`) rejected with `FILE_TYPE_UNSUPPORTED`; CSV formula injection characters (`=`, `+`, `@`) prepended with `'`. |
| **TC-21** | Network, Access & Secrets | S | COM-01, SR-2, SR-4, SR-6 | **PASS** | Server bound to `127.0.0.1`; no external network calls; `.gitignore` verified; zero credentials or raw participant data committed. |
| **TC-22** | Resource Logging & Limit | NF | NFR-11 | **PASS** | Runtime and peak memory logged via `psutil`; enforced memory limit failure handled gracefully without corrupting earlier runs. |

---

## 3. UI Browser Inspection Evidence

Automated headless Chrome sessions captured screenshots across all navigation views and responsive breakpoints:
1. `desktop_overview.png` (1366&times;768): Purpose, NHANES cycle, model badges, and warning banner.
2. `desktop_dataset.png` (1366&times;768): Dataset row/col stats, validation status, shared feature definitions.
3. `desktop_run.png` (1366&times;768): Model checkboxes, seed configuration, real-time progress monitors.
4. `desktop_comparison.png` (1366&times;768): Aligned comparison table, SVG metric bar charts, ROC curves, confusion matrices.
5. `desktop_details.png` (1366&times;768): Hyperparameters, quantum circuit diagram, limitations, library versions.
6. `desktop_predict.png` (1366&times;768): Interactive 5-parameter estimate form with client-side validation.
7. `desktop_predict_result.png` (1366&times;768): Computed probability score, predicted class, threshold, and warning.
8. `desktop_export.png` (1366&times;768): JSON/CSV/HTML export controls and aggregate JSON preview.
9. `mobile_overview.png`, `mobile_comparison.png`, `mobile_predict.png` (375&times;667): Responsive layout verified without clipping or overflow.
