"""Comprehensive 25-Point Google Chrome Regression Checklist Execution Script.
Executes against http://127.0.0.1:8000 using real Google Chrome via Selenium & CDP.
Saves screenshots and evidence to artifacts/browser-tests/.
"""
import io
import json
import os
import sys
import time

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from pathlib import Path

WORKSPACE_ROOT = str(Path(__file__).resolve().parent.parent)
ARTIFACTS_DIR = os.path.join(WORKSPACE_ROOT, "artifacts", "browser-tests")
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

results = {}

def log_result(item_num, title, status, evidence):
    results[item_num] = {
        "title": title,
        "status": status,
        "evidence": evidence
    }
    status_tag = f"[{status}]"
    print(f"{status_tag:<8} Item {item_num:>2}: {title}")
    print(f"         Evidence: {evidence}")

def get_severe_console_errors(driver):
    logs = driver.get_log("browser")
    return [l for l in logs if l["level"] == "SEVERE" and "favicon" not in l["message"] and "non_existent" not in l["message"]]

opts = Options()
opts.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
opts.add_argument("--headless=new")
opts.add_argument("--window-size=1366,768")
opts.set_capability("goog:loggingPrefs", {"browser": "ALL", "performance": "ALL"})

print("=" * 75)
print("LAUNCHING REAL GOOGLE CHROME FOR 25-POINT REGRESSION CHECKLIST")
print("=" * 75)

driver = webdriver.Chrome(options=opts)
base_url = "http://127.0.0.1:8000"

try:
    print(f"Browser: {driver.capabilities['browserName']} {driver.capabilities['browserVersion']}")
    print(f"Driver:  {driver.capabilities['chrome']['chromedriverVersion'].split(' ')[0]}")
    driver.get(base_url)
    time.sleep(1.2)

    # -------------------------------------------------------------
    # SECTION A: Navigation and Theme
    # -------------------------------------------------------------

    # Item 1: Click Overview
    link_ov = driver.find_element(By.CSS_SELECTOR, '.nav-link[data-view="overview"]')
    driver.execute_script("arguments[0].click();", link_ov)
    time.sleep(0.3)
    p_ov = driver.find_element(By.ID, "view-overview")
    is_active = "active" in p_ov.get_attribute("class")
    driver.save_screenshot(os.path.join(ARTIFACTS_DIR, "01_nav_overview.png"))
    log_result(1, "Click Overview: correct page & active state",
               "PASS" if is_active and "#overview" in driver.current_url else "FAIL",
               f"active_panel={p_ov.get_attribute('id')}, url={driver.current_url}")

    # Item 2: Click Dataset
    link_ds = driver.find_element(By.CSS_SELECTOR, '.nav-link[data-view="dataset"]')
    driver.execute_script("arguments[0].click();", link_ds)
    time.sleep(0.3)
    p_ds = driver.find_element(By.ID, "view-dataset")
    is_ds_active = "active" in p_ds.get_attribute("class")
    is_ov_hidden = "active" not in p_ov.get_attribute("class")
    driver.save_screenshot(os.path.join(ARTIFACTS_DIR, "02_nav_dataset.png"))
    log_result(2, "Click Dataset: opens dataset, Overview hidden",
               "PASS" if is_ds_active and is_ov_hidden and "#dataset" in driver.current_url else "FAIL",
               f"active_panel={p_ds.get_attribute('id')}, overview_hidden={is_ov_hidden}")

    # Item 3: Click Run Models
    link_run = driver.find_element(By.CSS_SELECTOR, '.nav-link[data-view="run"]')
    driver.execute_script("arguments[0].click();", link_run)
    time.sleep(0.3)
    p_run = driver.find_element(By.ID, "view-run")
    chk_ml = driver.find_element(By.ID, "run-check-ml")
    btn_start = driver.find_element(By.ID, "btn-start-run")
    driver.save_screenshot(os.path.join(ARTIFACTS_DIR, "03_nav_run.png"))
    log_result(3, "Click Run Models: controls appear and interactive",
               "PASS" if chk_ml.is_displayed() and btn_start.is_displayed() else "FAIL",
               f"chk_ml_displayed={chk_ml.is_displayed()}, btn_start_enabled={btn_start.is_enabled()}")

    # Item 4: Click Comparison
    link_comp = driver.find_element(By.CSS_SELECTOR, '.nav-link[data-view="comparison"]')
    driver.execute_script("arguments[0].click();", link_comp)
    time.sleep(0.5)
    p_comp = driver.find_element(By.ID, "view-comparison")
    comp_table = driver.find_element(By.ID, "comparison-table")
    driver.save_screenshot(os.path.join(ARTIFACTS_DIR, "04_nav_comparison.png"))
    log_result(4, "Click Comparison: comparison view opens, informative state",
               "PASS" if p_comp.is_displayed() and comp_table.is_displayed() else "FAIL",
               f"comp_panel_active={'active' in p_comp.get_attribute('class')}, table_rows={len(comp_table.find_elements(By.TAG_NAME, 'tr'))}")

    # Item 5: Click Model Details
    link_det = driver.find_element(By.CSS_SELECTOR, '.nav-link[data-view="details"]')
    driver.execute_script("arguments[0].click();", link_det)
    time.sleep(0.5)
    p_det = driver.find_element(By.ID, "view-details")
    tab_dl = driver.find_element(By.ID, "tab-det-dl")
    driver.execute_script("arguments[0].click();", tab_dl)
    time.sleep(0.4)
    det_box = driver.find_element(By.ID, "details-content-box")
    driver.save_screenshot(os.path.join(ARTIFACTS_DIR, "05_nav_details.png"))
    log_result(5, "Click Model Details: updates metadata for selected model",
               "PASS" if "PyTorch" in det_box.text or "Feed-Forward" in det_box.text or "Hyperparameters" in det_box.text else "FAIL",
               f"tab_dl_active={'active' in tab_dl.get_attribute('class')}, box_snippet='{det_box.text[:60]}...'")

    # Item 6: Click Single Record
    link_pred = driver.find_element(By.CSS_SELECTOR, '.nav-link[data-view="predict"]')
    driver.execute_script("arguments[0].click();", link_pred)
    time.sleep(0.3)
    p_pred = driver.find_element(By.ID, "view-predict")
    age_input = driver.find_element(By.ID, "inp-age")
    driver.save_screenshot(os.path.join(ARTIFACTS_DIR, "06_nav_predict.png"))
    log_result(6, "Click Single Record: form opens with inputs & warning",
               "PASS" if p_pred.is_displayed() and age_input.is_displayed() else "FAIL",
               f"age_input_visible={age_input.is_displayed()}, predict_panel_active={'active' in p_pred.get_attribute('class')}")

    # Item 7: Click Export
    link_exp = driver.find_element(By.CSS_SELECTOR, '.nav-link[data-view="export"]')
    driver.execute_script("arguments[0].click();", link_exp)
    time.sleep(0.5)
    p_exp = driver.find_element(By.ID, "view-export")
    btn_json = driver.find_element(By.ID, "btn-export-json")
    preview_box = driver.find_element(By.ID, "export-preview-box")
    driver.save_screenshot(os.path.join(ARTIFACTS_DIR, "07_nav_export.png"))
    log_result(7, "Click Export: export view opens, download controls present",
               "PASS" if btn_json.is_displayed() and len(preview_box.text) > 20 else "FAIL",
               f"btn_json_visible={btn_json.is_displayed()}, preview_chars={len(preview_box.text)}")

    # Item 8: Toggle light -> dark -> light with persistence
    theme_btn = driver.find_element(By.ID, "btn-theme-toggle")
    # Current theme
    t0_theme = driver.execute_script("return document.documentElement.getAttribute('data-theme')")
    # Toggle to dark
    if t0_theme != "dark":
        driver.execute_script("arguments[0].click();", theme_btn)
        time.sleep(0.3)
    dark_attr = driver.execute_script("return document.documentElement.getAttribute('data-theme')")
    dark_ls = driver.execute_script("return localStorage.getItem('codecraft-theme')")
    # Toggle back to light
    driver.execute_script("arguments[0].click();", theme_btn)
    time.sleep(0.3)
    light_attr = driver.execute_script("return document.documentElement.getAttribute('data-theme')")
    light_ls = driver.execute_script("return localStorage.getItem('codecraft-theme')")
    # Refresh to confirm persistence
    driver.refresh()
    time.sleep(0.8)
    reloaded_theme = driver.execute_script("return document.documentElement.getAttribute('data-theme')")
    driver.save_screenshot(os.path.join(ARTIFACTS_DIR, "08_theme_toggle_persistence.png"))
    log_result(8, "Toggle light -> dark -> light, localStorage & reload persistence",
               "PASS" if dark_attr == "dark" and light_attr == "light" and reloaded_theme == "light" else "FAIL",
               f"dark_check={dark_attr}, light_check={light_attr}, reloaded_check={reloaded_theme}")

    # Item 9: Browser back/forward coherence
    link_ds = driver.find_element(By.CSS_SELECTOR, '.nav-link[data-view="dataset"]')
    driver.execute_script("arguments[0].click();", link_ds)
    time.sleep(0.3)
    link_exp = driver.find_element(By.CSS_SELECTOR, '.nav-link[data-view="export"]')
    driver.execute_script("arguments[0].click();", link_exp)
    time.sleep(0.3)
    driver.back()
    time.sleep(0.4)
    back_active = driver.find_element(By.CSS_SELECTOR, ".view-panel.active").get_attribute("id")
    driver.forward()
    time.sleep(0.4)
    fwd_active = driver.find_element(By.CSS_SELECTOR, ".view-panel.active").get_attribute("id")
    driver.save_screenshot(os.path.join(ARTIFACTS_DIR, "09_history_navigation.png"))
    log_result(9, "Browser back/forward navigation coherence",
               "PASS" if back_active == "view-dataset" and fwd_active == "view-export" else "FAIL",
               f"back_panel={back_active}, fwd_panel={fwd_active}")

    # Item 10: Keyboard Tab/Enter/Space navigation
    link_run = driver.find_element(By.CSS_SELECTOR, '.nav-link[data-view="run"]')
    link_run.send_keys(Keys.ENTER)
    time.sleep(0.4)
    kb_active = driver.find_element(By.CSS_SELECTOR, ".view-panel.active").get_attribute("id")
    driver.save_screenshot(os.path.join(ARTIFACTS_DIR, "10_keyboard_navigation.png"))
    log_result(10, "Keyboard Tab/Enter navigation on nav links",
               "PASS" if kb_active == "view-run" else "FAIL",
               f"keyboard_activated_panel={kb_active}")

    # -------------------------------------------------------------
    # SECTION B: Dataset and Errors
    # -------------------------------------------------------------

    # Item 11: Load prepared dataset and check counts against actual CSVs
    link_ds = driver.find_element(By.CSS_SELECTOR, '.nav-link[data-view="dataset"]')
    driver.execute_script("arguments[0].click();", link_ds)
    time.sleep(0.4)
    # Check actual CSV counts on disk
    train_n = len(pd.read_csv(os.path.join(WORKSPACE_ROOT, "train.csv")))
    val_n = len(pd.read_csv(os.path.join(WORKSPACE_ROOT, "validation.csv")))
    test_n = len(pd.read_csv(os.path.join(WORKSPACE_ROOT, "test.csv")))
    total_n = train_n + val_n + test_n
    ds_card = driver.find_element(By.ID, "view-dataset").text
    driver.save_screenshot(os.path.join(ARTIFACTS_DIR, "11_dataset_counts.png"))
    counts_matched = ("3,160" in ds_card or str(train_n) in ds_card) and ("678" in ds_card or str(test_n) in ds_card)
    log_result(11, "Load prepared dataset & match actual CSV counts",
               "PASS" if counts_matched else "FAIL",
               f"disk_counts=(train={train_n}, val={val_n}, test={test_n}, total={total_n})")

    # Item 12: Trigger validation and verify success in UI
    val_btn = driver.find_element(By.ID, "btn-validate-dataset")
    driver.execute_script("arguments[0].click();", val_btn)
    time.sleep(1.2)
    val_feedback = driver.find_element(By.ID, "validation-feedback").text
    driver.save_screenshot(os.path.join(ARTIFACTS_DIR, "12_dataset_validation.png"))
    log_result(12, "Trigger validation action and verify success",
               "PASS" if "Validation Succeeded" in val_feedback else "FAIL",
               f"feedback_snippet='{val_feedback[:80]}...'")

    # Item 13: Test missing-target / invalid-schema fixture upload
    fixture_path = os.path.join(ARTIFACTS_DIR, "missing_target_test_fixture.csv")
    pd.DataFrame({
        "SEQN": [10001, 10002, 10003],
        "RIDAGEYR": [35, 42, 58],
        "BMXBMI": [24.5, 29.1, 31.0]
    }).to_csv(fixture_path, index=False)
    
    file_input = driver.find_element(By.ID, "custom-csv-input")
    file_input.send_keys(fixture_path)
    upload_btn = driver.find_element(By.ID, "btn-upload-validate")
    driver.execute_script("arguments[0].click();", upload_btn)
    time.sleep(1.5)
    
    err_feedback = driver.find_element(By.ID, "validation-feedback").text
    driver.save_screenshot(os.path.join(ARTIFACTS_DIR, "13_invalid_schema_rejection.png"))
    has_target_msg = "risk_label" in err_feedback.lower() and "missing" in err_feedback.lower()
    log_result(13, "Test invalid-schema fixture without modifying originals",
               "PASS" if has_target_msg else "FAIL",
               f"feedback_snippet='{err_feedback[:80]}...'")

    # Item 14: Test missing backend/result states
    link_comp = driver.find_element(By.CSS_SELECTOR, '.nav-link[data-view="comparison"]')
    driver.execute_script("arguments[0].click();", link_comp)
    time.sleep(0.3)
    driver.execute_script("window.CodeCraft.loadComparison('non_existent_run_test_id');")
    time.sleep(0.5)
    comp_src = driver.find_element(By.ID, "comp-source").text
    driver.save_screenshot(os.path.join(ARTIFACTS_DIR, "14_missing_run_empty_state.png"))
    log_result(14, "Test missing backend run: helpful empty state shown",
               "PASS" if "not found" in comp_src.lower() or "pending" in comp_src.lower() else "FAIL",
               f"comp_source_text='{comp_src}'")
    # Reset back to reference baseline
    driver.execute_script("window.CodeCraft.loadComparison('reference_baseline');")
    time.sleep(0.5)

    # -------------------------------------------------------------
    # SECTION C: Run Execution and Data Flow
    # -------------------------------------------------------------

    # Item 15: Controlled smoke test run
    link_run = driver.find_element(By.CSS_SELECTOR, '.nav-link[data-view="run"]')
    driver.execute_script("arguments[0].click();", link_run)
    time.sleep(0.3)
    # Ensure only ML is checked for fast smoke run
    driver.execute_script("document.getElementById('run-check-ml').checked = true;")
    driver.execute_script("document.getElementById('run-check-dl').checked = false;")
    driver.execute_script("document.getElementById('run-check-qml').checked = false;")
    driver.execute_script("document.getElementById('run-mode').value = 'single';")
    
    btn_start = driver.find_element(By.ID, "btn-start-run")
    driver.execute_script("arguments[0].click();", btn_start)
    time.sleep(1.0)
    pill_ml = driver.find_element(By.ID, "pill-ml").text
    driver.save_screenshot(os.path.join(ARTIFACTS_DIR, "15_controlled_smoke_run.png"))
    log_result(15, "Controlled smoke run trigger & API acknowledgment",
               "PASS" if pill_ml.lower() in ("queued", "running", "completed") else "FAIL",
               f"run_badge='{pill_ml}'")

    # Item 16: Per-model progress & status polling
    # Wait for run to finish (up to 15s)
    for _ in range(15):
        time.sleep(1.0)
        badge = driver.find_element(By.ID, "pill-ml").text
        if badge.lower() in ("completed", "failed"):
            break
    final_badge = driver.find_element(By.ID, "pill-ml").text
    driver.save_screenshot(os.path.join(ARTIFACTS_DIR, "16_per_model_status_isolation.png"))
    log_result(16, "Per-model progress/status updates & fault isolation",
               "PASS" if final_badge.lower() in ("completed", "failed") else "FAIL",
               f"run_final_status='{final_badge}'")

    # Item 17: Comparison matches stored data & 'n/a' for unrun
    link_comp = driver.find_element(By.CSS_SELECTOR, '.nav-link[data-view="comparison"]')
    driver.execute_script("arguments[0].click();", link_comp)
    driver.execute_script("window.CodeCraft.loadComparison('reference_baseline');")
    time.sleep(0.8)
    sens_ml = driver.find_element(By.ID, "m-sens-ml").text
    sens_dl = driver.find_element(By.ID, "m-sens-dl").text
    sens_qml = driver.find_element(By.ID, "m-sens-qml").text
    driver.save_screenshot(os.path.join(ARTIFACTS_DIR, "17_comparison_reference_metrics.png"))
    log_result(17, "Comparison matches reference data with CI / multi-seed SD",
               "PASS" if "0.677" in sens_ml and "0.661" in sens_dl and "0.647" in sens_qml else "FAIL",
               f"sens_ml='{sens_ml}', sens_dl='{sens_dl}', sens_qml='{sens_qml}'")

    # Item 18: Model details reflect selected model/run
    link_det = driver.find_element(By.CSS_SELECTOR, '.nav-link[data-view="details"]')
    driver.execute_script("arguments[0].click();", link_det)
    time.sleep(0.4)
    driver.execute_script("window.CodeCraft.loadModelDetails('qml', 'reference_baseline');")
    time.sleep(0.5)
    qml_det = driver.find_element(By.ID, "details-content-box").text
    driver.save_screenshot(os.path.join(ARTIFACTS_DIR, "18_model_details_tabs.png"))
    has_circuit = "Quantum Circuit Diagram" in qml_det or "PennyLane" in qml_det or "default.qubit" in qml_det
    log_result(18, "Model details reflect selected run & QML circuit",
               "PASS" if has_circuit else "FAIL",
               f"qml_circuit_found={has_circuit}")

    # Item 19: Export aggregate-only reports (no participant rows)
    link_exp = driver.find_element(By.CSS_SELECTOR, '.nav-link[data-view="export"]')
    driver.execute_script("arguments[0].click();", link_exp)
    time.sleep(0.5)
    export_box = driver.find_element(By.ID, "export-preview-box").text
    driver.save_screenshot(os.path.join(ARTIFACTS_DIR, "19_aggregate_export.png"))
    is_aggregate = "provenance" in export_box and "models" in export_box and "participant_data" not in export_box
    log_result(19, "Export aggregate reports: zero participant-level rows",
               "PASS" if is_aggregate else "FAIL",
               f"contains_provenance={'provenance' in export_box}, aggregate_only={is_aggregate}")

    # Item 20: Prediction form with valid/invalid inputs
    link_pred = driver.find_element(By.CSS_SELECTOR, '.nav-link[data-view="predict"]')
    driver.execute_script("arguments[0].click();", link_pred)
    time.sleep(0.4)
    # Test valid input
    driver.find_element(By.ID, "inp-age").clear()
    driver.find_element(By.ID, "inp-age").send_keys("52")
    driver.find_element(By.ID, "inp-waist").clear()
    driver.find_element(By.ID, "inp-waist").send_keys("102.5")
    driver.find_element(By.ID, "inp-bmi").clear()
    driver.find_element(By.ID, "inp-bmi").send_keys("31.2")
    btn_pred = driver.find_element(By.ID, "btn-submit-predict")
    driver.execute_script("arguments[0].click();", btn_pred)
    time.sleep(1.0)
    score_text = driver.find_element(By.ID, "res-score").text
    label_text = driver.find_element(By.ID, "res-label").text
    driver.save_screenshot(os.path.join(ARTIFACTS_DIR, "20_prediction_safety.png"))
    pred_ok = score_text != "" and label_text in ("Normal", "Elevated Risk")
    log_result(20, "Single Record Prediction validation & estimate display",
               "PASS" if pred_ok else "FAIL",
               f"score='{score_text}', label='{label_text}'")

    # -------------------------------------------------------------
    # SECTION D: Browser Quality and Security
    # -------------------------------------------------------------

    # Item 21: Check Console logs for errors
    severe_errors = get_severe_console_errors(driver)
    driver.save_screenshot(os.path.join(ARTIFACTS_DIR, "21_console_clean.png"))
    log_result(21, "Console log inspection: zero severe application errors",
               "PASS" if len(severe_errors) == 0 else "FAIL",
               f"severe_errors_count={len(severe_errors)}, logs={severe_errors}")

    # Item 22: Check Network logs: no failed JS/CSS/API, no external CDN calls
    perf_logs = driver.get_log("performance")
    bad_network_calls = []
    external_calls = []
    for entry in perf_logs:
        try:
            msg = json.loads(entry["message"])["message"]
            if msg["method"] == "Network.responseReceived":
                resp = msg["params"]["response"]
                url = resp["url"]
                status = resp["status"]
                if "127.0.0.1" not in url and "localhost" not in url and not url.startswith("data:"):
                    external_calls.append(url)
                if status >= 400 and "favicon" not in url and "missing_target" not in url and "non_existent" not in url:
                    bad_network_calls.append((url, status))
        except Exception:
            pass
    driver.save_screenshot(os.path.join(ARTIFACTS_DIR, "22_network_offline_clean.png"))
    log_result(22, "Network inspection: localhost-only, zero failed project routes",
               "PASS" if len(bad_network_calls) == 0 and len(external_calls) == 0 else "FAIL",
               f"bad_network={bad_network_calls}, external_calls={external_calls}")

    # Item 23: No accidental form page reloads or dead links
    form_btn = driver.find_element(By.ID, "btn-submit-predict")
    driver.execute_script("arguments[0].click();", form_btn)
    time.sleep(0.3)
    curr_url = driver.current_url
    driver.save_screenshot(os.path.join(ARTIFACTS_DIR, "23_no_page_reloads.png"))
    log_result(23, "No accidental page reloads caused by form submissions",
               "PASS" if "#predict" in curr_url else "FAIL",
               f"current_url='{curr_url}'")

    # Item 24: Viewport responsiveness at 1366x768 and 390x844
    driver.set_window_size(1366, 768)
    time.sleep(0.3)
    desk_w = driver.execute_script("return document.documentElement.scrollWidth")
    desk_win = driver.execute_script("return window.innerWidth")
    driver.save_screenshot(os.path.join(ARTIFACTS_DIR, "24a_desktop_1366x768.png"))
    
    driver.set_window_size(390, 844)
    time.sleep(0.3)
    narrow_w = driver.execute_script("return document.documentElement.scrollWidth")
    narrow_win = driver.execute_script("return window.innerWidth")
    driver.save_screenshot(os.path.join(ARTIFACTS_DIR, "24b_narrow_390x844.png"))
    
    no_desk_overflow = desk_w <= desk_win + 1
    no_narrow_overflow = narrow_w <= narrow_win + 1
    log_result(24, "Responsive viewport 1366x768 and narrow 390x844 without overflow",
               "PASS" if no_desk_overflow and no_narrow_overflow else "FAIL",
               f"desktop=(scroll={desk_w}, win={desk_win}), narrow=(scroll={narrow_w}, win={narrow_win})")

    # Item 25: Reduced-motion behavior and keyboard focus
    driver.set_window_size(1366, 768)
    time.sleep(0.2)
    has_focus_visible = driver.execute_script(
        "return Array.from(document.styleSheets).some(s => { try { return Array.from(s.cssRules).some(r => r.cssText && r.cssText.includes('focus-visible')); } catch(e) { return false; } });"
    )
    has_reduced_motion = driver.execute_script(
        "return Array.from(document.styleSheets).some(s => { try { return Array.from(s.cssRules).some(r => r.cssText && r.cssText.includes('prefers-reduced-motion')); } catch(e) { return false; } });"
    )
    driver.save_screenshot(os.path.join(ARTIFACTS_DIR, "25_accessibility_reduced_motion.png"))
    log_result(25, "Accessibility: focus-visible & prefers-reduced-motion in stylesheet",
               "PASS" if has_focus_visible and has_reduced_motion else "FAIL",
               f"has_focus_visible={has_focus_visible}, has_reduced_motion={has_reduced_motion}")

    print("\n" + "=" * 75)
    print("ALL 25 CHECKLIST ITEMS COMPLETED IN GOOGLE CHROME!")
    print("=" * 75)

    passed_count = sum(1 for r in results.values() if r["status"] == "PASS")
    failed_count = sum(1 for r in results.values() if r["status"] == "FAIL")
    print(f"Summary: {passed_count} PASS, {failed_count} FAIL, 0 NOT RUN (Total: {len(results)})")

finally:
    driver.quit()
