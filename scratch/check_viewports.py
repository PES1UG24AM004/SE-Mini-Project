import os
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

WORKSPACE_ROOT = str(Path(__file__).resolve().parent.parent)
OUT_DIR = os.path.join(WORKSPACE_ROOT, "artifacts", "responsive-previews")
os.makedirs(OUT_DIR, exist_ok=True)

opts = Options()
opts.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
opts.add_argument("--headless=new")
opts.add_argument("--window-size=1440,900")

driver = webdriver.Chrome(options=opts)
base_url = "http://127.0.0.1:8000"

viewports = [
    ("desktop-1440", 1440, 900),
    ("desktop-1024", 1024, 768),
    ("tablet-768", 768, 1024),
    ("mobile-390", 390, 844),
    ("mobile-360", 360, 740),
]

views = ["overview", "dataset", "run", "comparison", "details", "predict", "export"]

print("=" * 70)
print("CHECKING MULTI-VIEWPORT RESPONSIVENESS (1440px, 1024px, 768px, 390px, 360px)")
print("=" * 70)

all_ok = True
for vp_name, w, h in viewports:
    driver.set_window_size(w, h)
    time.sleep(0.3)
    for v in views:
        driver.get(f"{base_url}/#{v}")
        time.sleep(0.3)
        win_w = driver.execute_script("return window.innerWidth")
        doc_w = driver.execute_script("return document.documentElement.scrollWidth")
        has_overflow = doc_w > win_w + 1
        if has_overflow:
            all_ok = False
            print(f"[OVERFLOW] {vp_name:<14} View #{v:<12}: win={win_w}, doc={doc_w}")
        else:
            print(f"[OK]       {vp_name:<14} View #{v:<12}: win={win_w}, doc={doc_w}")
        
        # Save selective screenshots for documentation
        if v in ("overview", "comparison", "predict"):
            driver.save_screenshot(os.path.join(OUT_DIR, f"{vp_name}_{v}.png"))

# Also capture dark mode comparison & overview
driver.set_window_size(1440, 900)
driver.get(f"{base_url}/#overview")
time.sleep(0.3)
driver.execute_script("document.documentElement.setAttribute('data-theme', 'dark');")
time.sleep(0.3)
driver.save_screenshot(os.path.join(OUT_DIR, "desktop-1440_overview_dark.png"))
driver.get(f"{base_url}/#comparison")
time.sleep(0.3)
driver.save_screenshot(os.path.join(OUT_DIR, "desktop-1440_comparison_dark.png"))

print("=" * 70)
res_text = "ALL PASSED (0 OVERFLOW)" if all_ok else "SOME OVERFLOW DETECTED"
print(f"ALL VIEWPORTS RESULT: {res_text}")
print("=" * 70)

driver.quit()
