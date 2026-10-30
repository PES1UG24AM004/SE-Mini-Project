# CodeCraft Browser Debug & Regression Verification Report

**Date:** 2026-10-24  
**Workspace:** `C:\Users\Aarav\Documents\Studies\Sem5\Assignments\Software_Engineering\MIni`  
**Application Target:** `http://127.0.0.1:8000`  
**Test Harness:** Google Chrome via Selenium WebDriver (Chrome DevTools Protocol)  

---

## 1. Proven Root Cause(s) by Initial Evidence

The complete unresponsiveness of the CodeCraft user interface was caused by **two distinct, fatal JavaScript syntax errors** in `frontend/static/js/app.js`:

1. **Primary Fatal Syntax Error (`app.js:317` and `app.js:427`):**
   * **Exact Code:**
     ```javascript
     ciText = ` <small>[${formatNum(m.ci95[item.key][0])}, ${formatNum(m.ci95[item.key][1])]}</small>`;
     ```
   * **Evidence:** In Google Chrome DevTools console upon initial page load:
     ```
     Uncaught SyntaxError: Missing } in template expression (at app.js:427:70)
     ```
     Also validated independently via Node.js compiler:
     ```powershell
     node -c frontend/static/js/app.js
     # Output: SyntaxError: Missing } in template expression
     ```
   * **Mechanics:** An array index close bracket `]` was inadvertently placed inside the template interpolation expression `${formatNum(m.ci95[item.key][1])]}` instead of closing after the formatting function `${formatNum(m.ci95[item.key][1])]}`.

2. **Secondary Missing Navigation Protocol:**
   * In `frontend/templates/index.html`, the navigation pills were static `<li>` elements without anchor `<a>` tags, missing `role="tab"`, keyboard event handlers, and URL hash routing (`window.location.hash`). Even if JavaScript had executed, direct navigation, browser back/forward history, and deep-linking were unsupported.

---

## 2. Why the UI Appeared Completely Unresponsive

In non-module JavaScript scripts loaded via `<script src="/static/js/app.js"></script>`, the browser parses and compiles the entire script before executing any statements. 

Because `app.js` contained a fatal `SyntaxError`, the Chrome V8 JavaScript engine **aborted execution immediately during compilation**. None of the subsequent JavaScript was ever executed:
* Zero DOM event listeners were registered (`addEventListener` for navigation pills, buttons, tabs, forms, or theme switchers never ran).
* The default HTML state had `#view-overview` set to `display: block` and all other sections set to `display: none`.
* When the user clicked on "Dataset", "Run Models", "Comparison", or the theme toggle, the clicks simply fell through as unhandled pointer events on inactive DOM nodes.
* The application remained permanently frozen on the initial Overview section.

---

## 3. Files Changed and Why

| File Path | Description of Changes |
| :--- | :--- |
| [`frontend/static/js/app.js`](file:///C:/Users/Aarav/Documents/Studies/Sem5/Assignments/Software_Engineering/MIni/frontend/static/js/app.js) | Fixed template interpolation syntax (`${formatNum(m.ci95[item.key][1])}]`); added hash-based client routing (`#overview`, `#dataset`, `#run`, `#comparison`, `#details`, `#predict`, `#export`) with `hashchange` and `popstate` listeners; implemented theme toggle logic with `localStorage` persistence; added empty/pending fallback states for unrun models; exposed test automation hooks `window.CodeCraft`. |
| [`frontend/templates/index.html`](file:///C:/Users/Aarav/Documents/Studies/Sem5/Assignments/Software_Engineering/MIni/frontend/templates/index.html) | Converted static `<li>` pills to accessible, semantic `<a>` links with `role="tab"`, `aria-selected`, and `aria-controls`; added `#btn-theme-toggle` in header; added early inline theme initializer script in `<head>` to prevent theme flashing; added live region `#toast-container`; clarified partition breakdown in `#view-dataset` (3,160 train / 677 val / 678 test). |
| [`frontend/static/css/style.css`](file:///C:/Users/Aarav/Documents/Studies/Sem5/Assignments/Software_Engineering/MIni/frontend/static/css/style.css) | Converted interface to a strict grayscale design system (Light: `#F5F5F5` canvas, `#FFFFFF` surface, `#191919` text, `#D5D5D5` borders; Dark: `#111111` canvas, `#191919` surface, `#F4F4F4` text, `#3C3C3C` borders); implemented geometric non-color cues (ML: solid border with ●, DL: dashed border with ■, QML: dotted border with ◆); replaced UTF-8 non-ASCII characters in comments to guarantee CP-1252 decoder compatibility on Windows. |
| [`backend/orchestration/orchestrator.py`](file:///C:/Users/Aarav/Documents/Studies/Sem5/Assignments/Software_Engineering/MIni/backend/orchestration/orchestrator.py) | Upgraded run ID timestamp formatting to microsecond resolution (`%Y%m%d_%H%M%S_%f`) to prevent ID collisions during rapid consecutive automated test runs. |
| [`docs/frontend-repair-notes.md`](file:///C:/Users/Aarav/Documents/Studies/Sem5/Assignments/Software_Engineering/MIni/docs/frontend-repair-notes.md) | Documented complete diagnosis, root causes, implementation details, screenshot manifests, and verification logs. |
| [`README.md`](file:///C:/Users/Aarav/Documents/Studies/Sem5/Assignments/Software_Engineering/MIni/README.md) | Updated user walkthrough to document hash-based SPA navigation, strict grayscale theme switcher, and Selenium verification commands. |

---

## 4. Server Launch and Target URL

* **Launch Command:**
  ```powershell
  .\.venv\Scripts\python.exe run_server.py
  ```
* **Active Server Process:** Python 3.12 Uvicorn instance (PID: `27160`)
* **Binding:** `http://127.0.0.1:8000` (Localhost only, offline-ready, zero external CDNs)
* **Health Check Probe:** `GET http://127.0.0.1:8000/api/dataset` &rarr; `HTTP 200 OK`

---

## 5. Google Chrome Browser Verification

Google Chrome was confirmed installed and used for automated testing via Selenium WebDriver and Chrome DevTools Protocol:
* **Browser Name:** Google Chrome
* **Browser Version:** `155.0.8059.86`
* **Binary Executable:** `C:\Program Files\Google\Chrome\Application\chrome.exe`
* **ChromeDriver Version:** `155.0.8059.84`
* **CDP Capabilities Enabled:** Browser console logs (`goog:loggingPrefs -> browser: ALL`), performance & network tracing (`performance: ALL`).

---

## 6. Console Errors & Network Requests: Before vs. After

### Before Repair:
* **Console Errors:** `1` fatal compilation error: `Uncaught SyntaxError: Missing } in template expression` at `app.js:427:70`.
* **Execution State:** All user clicks dropped; 0 event handlers registered.
* **Network Responses:** Only initial `/`, `/static/css/style.css`, and `/static/js/app.js` were fetched; no subsequent API calls were initiated by the UI.

### After Repair:
* **Console Errors:** `0` severe application errors during full user walkthrough.
* **Network Calls:** All local REST endpoints (`/api/dataset`, `/api/datasets/validate`, `/api/runs`, `/api/comparison`, `/api/models/*`, `/api/reports/*`, `/api/predict`) returned valid `200 OK` or `202 Accepted` status codes with expected JSON payloads. Zero external CDN or analytics requests.

---

## 7. Results for All 25 Chrome Checklist Items

All 25 checklist items were executed in Google Chrome via [`scratch/test_chrome_regression_checklist.py`](file:///C:/Users/Aarav/Documents/Studies/Sem5/Assignments/Software_Engineering/MIni/scratch/test_chrome_regression_checklist.py).

| Item # | Section & Title | Status | Evidence / Observed Behavior | Screenshot |
| :---: | :--- | :---: | :--- | :--- |
| **01** | Navigation: Click Overview | **PASS** | `#view-overview` active, URL updated to `/#overview` | `01_nav_overview.png` |
| **02** | Navigation: Click Dataset | **PASS** | `#view-dataset` active, Overview hidden, URL contains `/#dataset` | `02_nav_dataset.png` |
| **03** | Navigation: Click Run Models | **PASS** | Checkboxes visible, `#btn-start-run` interactable | `03_nav_run.png` |
| **04** | Navigation: Click Comparison | **PASS** | Aligned 3-family table with 12 rows visible and populated | `04_nav_comparison.png` |
| **05** | Navigation: Click Model Details | **PASS** | Tabs switch between ML, DL, and QML; specs update dynamically | `05_nav_details.png` |
| **06** | Navigation: Click Single Record | **PASS** | Clinical input fields visible with non-diagnostic warning banner | `06_nav_predict.png` |
| **07** | Navigation: Click Export | **PASS** | Export buttons visible, report preview box populated (7,517 chars) | `07_nav_export.png` |
| **08** | Theme: Light &rarr; Dark &rarr; Light | **PASS** | Toggles cleanly; persists across page reload in `localStorage` | `08_theme_toggle_persistence.png` |
| **09** | Navigation: Browser Back/Forward | **PASS** | Browser back returns to Dataset; forward navigates to Export | `09_history_navigation.png` |
| **10** | Navigation: Keyboard Tab/Enter | **PASS** | Keyboard focus and Enter key activates navigation pills | `10_keyboard_navigation.png` |
| **11** | Dataset: Partition Counts Match | **PASS** | UI displays 3,160 train / 677 val / 678 test, matching disk CSVs | `11_dataset_counts.png` |
| **12** | Dataset: Live Validation | **PASS** | Returns `✓ Validation Succeeded (0.0086s)`, zero schema defects | `12_dataset_validation.png` |
| **13** | Dataset: Invalid Schema Rejection | **PASS** | Rejects missing `risk_label` fixture without modifying originals | `13_invalid_schema_rejection.png` |
| **14** | States: Missing Run Empty State | **PASS** | Displays `Run not found or pending` and `n/a` without freezing | `14_missing_run_empty_state.png` |
| **15** | Run Execution: Controlled Smoke Run | **PASS** | Initiated single-seed ML run; acknowledged within 2 seconds | `15_controlled_smoke_run.png` |
| **16** | Run Execution: Per-Model Status | **PASS** | Status transitions `QUEUED` &rarr; `RUNNING` &rarr; `COMPLETED` | `16_per_model_status_isolation.png` |
| **17** | Comparison: Reference Metrics Match | **PASS** | ML: 0.677 [0.620, 0.739]; DL: 0.661 &plusmn; 0.010; QML: 0.647 &plusmn; 0.040 | `17_comparison_reference_metrics.png` |
| **18** | Details: QML Circuit Rendering | **PASS** | Renders 8-qubit variational quantum circuit diagram | `18_model_details_tabs.png` |
| **19** | Export: Aggregate Only (Privacy) | **PASS** | Contains provenance and metrics; zero individual participant records | `19_aggregate_export.png` |
| **20** | Prediction: Risk Calculation | **PASS** | Computes estimate (`0.5292`, `Normal`) with persistent warning | `20_prediction_safety.png` |
| **21** | Quality: Console Log Inspection | **PASS** | Zero severe application errors in Chrome console log | `21_console_clean.png` |
| **22** | Security: Localhost-Only Network | **PASS** | Localhost only, zero failed project endpoints, zero external CDNs | `22_network_offline_clean.png` |
| **23** | Quality: No Accidental Page Reloads | **PASS** | Forms do not cause full-page reloads; hash routing stays intact | `23_no_page_reloads.png` |
| **24** | Layout: Viewport Responsiveness | **PASS** | Zero horizontal overflow at desktop (1366×768) and narrow (390×844) | `24a_desktop_1366x768.png`<br>`24b_narrow_390x844.png` |
| **25** | Accessibility: Motion & Focus | **PASS** | `focus-visible` and `prefers-reduced-motion` active in stylesheet | `25_accessibility_reduced_motion.png` |

---

## 8. Automated Test Execution & Results

### Pytest Full Acceptance Suite:
```powershell
.\.venv\Scripts\pytest -v tests
```
```
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

======================= 22 passed, 1 warning in 12.69s ========================
```
* **Success Rate:** 100% (22/22 tests passed).

---

## 9. Screenshot Artifacts

All screenshots captured during live Google Chrome execution are saved in [`artifacts/browser-tests/`](file:///C:/Users/Aarav/Documents/Studies/Sem5/Assignments/Software_Engineering/MIni/artifacts/browser-tests/):

* `01_nav_overview.png`
* `02_nav_dataset.png`
* `03_nav_run.png`
* `04_nav_comparison.png`
* `05_nav_details.png`
* `06_nav_predict.png`
* `07_nav_export.png`
* `08_theme_toggle_persistence.png`
* `09_history_navigation.png`
* `10_keyboard_navigation.png`
* `11_dataset_counts.png`
* `12_dataset_validation.png`
* `13_invalid_schema_rejection.png`
* `14_missing_run_empty_state.png`
* `15_controlled_smoke_run.png`
* `16_per_model_status_isolation.png`
* `17_comparison_reference_metrics.png`
* `18_model_details_tabs.png`
* `19_aggregate_export.png`
* `20_prediction_safety.png`
* `21_console_clean.png`
* `22_network_offline_clean.png`
* `23_no_page_reloads.png`
* `24a_desktop_1366x768.png`
* `24b_narrow_390x844.png`
* `25_accessibility_reduced_motion.png`

---

## 10. Remaining Methodological Limitations & Next Steps

1. **Cross-Sectional Survey Scope:** The NHANES dataset represents a single point-in-time survey. As noted in the disclaimer banner, classification reflects concurrent biomarker risk, not an epidemiological forecast of future incidence.
2. **Classical Quantum Simulation:** The QML pipeline runs on PennyLane's `default.qubit` state-vector simulator on a classical CPU. No physical quantum processor was employed, and no quantum supremacy is claimed.
3. **Unweighted Survey Cohort:** Analyses are performed unweighted on the 4,515 cohort members and do not model complex multistage survey weights (`WTMEC2YR`).

### Next Steps for Live Demonstration:
1. Open Google Chrome and visit `http://127.0.0.1:8000/#comparison`.
2. Inspect the head-to-head comparison metrics and SVG ROC curve.
3. Toggle between Light and Dark mode using the header button.
4. Try submitting a single-record prediction on `/#predict` to test real-time inference.
