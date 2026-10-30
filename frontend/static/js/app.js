/**
 * CodeCraft Early Metabolic Risk Detection — Frontend Application
 * Local-first, vanilla JavaScript (no runtime CDN or third-party dependencies)
 * Features: Hash-based routing, strict grayscale theme toggle, real-time polling, and SVG charts.
 */

document.addEventListener("DOMContentLoaded", () => {
  // Current state
  let currentRunId = "reference_baseline";
  let pollTimeout = null;
  let consecutivePollErrors = 0;
  let currentModelTab = "ml";
  let latestComparisonData = null;

  // Elements
  const navLinks = document.querySelectorAll(".nav-link");
  const viewPanels = document.querySelectorAll(".view-panel");
  const themeToggleBtn = document.getElementById("btn-theme-toggle");
  const themeNameSpan = document.getElementById("theme-name");
  const toastContainer = document.getElementById("toast-container");

  // =========================================================================
  // 1. Toast Notification System
  // =========================================================================
  function showToast(message) {
    if (!toastContainer) return;
    const toast = document.createElement("div");
    toast.className = "toast";
    toast.setAttribute("role", "status");
    toast.innerHTML = `<span>&bull;</span> <span>${escapeHtml(message)}</span>`;
    toastContainer.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateY(8px)";
      setTimeout(() => toast.remove(), 240);
    }, 3200);
  }

  // =========================================================================
  // 2. Theme System (Light / Dark Mode Persistence)
  // =========================================================================
  function updateThemeUI(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    if (themeNameSpan) {
      themeNameSpan.textContent = theme === "dark" ? "Dark" : "Light";
    }
    try {
      localStorage.setItem("codecraft-theme", theme);
    } catch (e) {}

    // Synchronously re-render SVG charts using cached data without network round-trips (AUD-10)
    if (document.getElementById("view-comparison").classList.contains("active") && latestComparisonData) {
      const modelMap = {};
      (latestComparisonData.models || []).forEach((m) => {
        modelMap[m.family] = m;
      });
      renderBarChart(modelMap);
      renderRocChart(modelMap);
    }
  }

  function initTheme() {
    let saved = null;
    try {
      saved = localStorage.getItem("codecraft-theme");
    } catch (e) {}
    const systemDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    const initialTheme = saved ? saved : (systemDark ? "dark" : "light");
    updateThemeUI(initialTheme);
  }

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener("click", () => {
      const current = document.documentElement.getAttribute("data-theme") || "light";
      const next = current === "dark" ? "light" : "dark";
      updateThemeUI(next);
      showToast(`Switched to ${next} theme.`);
    });
  }

  // =========================================================================
  // 3. Hash-Based Client Routing & History Management
  // =========================================================================
  const validViews = ["overview", "dataset", "run", "comparison", "details", "predict", "export"];

  function switchView(viewName, updateHash = true) {
    const target = validViews.includes(viewName) ? viewName : "overview";

    navLinks.forEach((link) => {
      const match = link.getAttribute("data-view") === target;
      link.classList.toggle("active", match);
      link.setAttribute("aria-selected", match ? "true" : "false");
      if (match) {
        link.setAttribute("aria-current", "page");
      } else {
        link.removeAttribute("aria-current");
      }
    });

    viewPanels.forEach((panel) => {
      const match = panel.id === `view-${target}`;
      panel.classList.toggle("active", match);
    });

    if (updateHash && window.location.hash !== `#${target}`) {
      history.pushState(null, "", `#${target}`);
    }

    // View specific initializations
    if (target === "comparison") {
      loadComparison(currentRunId);
    } else if (target === "details") {
      loadModelDetails(currentModelTab, currentRunId);
    } else if (target === "export") {
      loadExportPreview(currentRunId);
    }
  }

  function handleRoute() {
    const hash = window.location.hash.replace("#", "").trim();
    switchView(hash || "overview", false);
  }

  window.addEventListener("hashchange", handleRoute);

  navLinks.forEach((link) => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      const targetView = link.getAttribute("data-view");
      switchView(targetView, true);
    });
  });

  // =========================================================================
  // 4. View 2: Dataset & Validation
  // =========================================================================
  const btnValidate = document.getElementById("btn-validate-dataset");
  const valFeedback = document.getElementById("validation-feedback");
  const btnUploadValidate = document.getElementById("btn-upload-validate");
  const customCsvInput = document.getElementById("custom-csv-input");
  const uploadStatusText = document.getElementById("upload-status-text");

  async function runDatasetValidation(file = null) {
    if (valFeedback) {
      valFeedback.innerHTML = "<em>Validating dataset schema, data types, physical ranges, and privacy...</em>";
    }
    if (btnValidate) btnValidate.disabled = true;
    if (btnUploadValidate) btnUploadValidate.disabled = true;

    try {
      let res;
      if (file) {
        const formData = new FormData();
        formData.append("file", file);
        res = await fetch("/api/datasets/validate", {
          method: "POST",
          body: formData,
        });
      } else {
        res = await fetch("/api/datasets/validate", { method: "POST" });
      }

      const data = await res.json();
      if (!res.ok || data.error) {
        const errMsg = data.error ? data.error.message : "Validation failed";
        valFeedback.innerHTML = `
          <div style="font-weight: 700; text-decoration: underline;">Validation Failed: ${escapeHtml(errMsg)}</div>
          <div style="font-size: 12px; margin-top: 4px; color: var(--text-secondary);">Error Code: <code>${escapeHtml(data.error?.code || 'ERROR')}</code></div>
        `;
        showToast("Validation identified errors.");
        return;
      }

      let issuesHtml = "";
      if (data.issues && data.issues.length > 0) {
        issuesHtml = `<ul style="margin: 6px 0 0 16px; padding: 0; font-size: 12px;">`;
        data.issues.forEach((iss) => {
          issuesHtml += `<li><strong>${escapeHtml(iss.field || "general")}:</strong> ${escapeHtml(iss.error || "")}</li>`;
        });
        issuesHtml += `</ul>`;
      }

      valFeedback.innerHTML = `
        <div style="font-weight: 700;">
          ${data.valid ? '&check; Validation Succeeded' : '&times; Validation Identified Issues'}
          <span style="font-size: 12px; font-weight: normal; color: var(--text-secondary);"> (Execution Time: ${data.validationTimeSec}s)</span>
        </div>
        <div style="font-size: 12px; margin-top: 4px; color: var(--text-secondary);">
          Source: <code>${escapeHtml(data.source)}</code> | Records: <strong>${data.rows?.toLocaleString()}</strong> | Columns: <strong>${data.columns}</strong>
          ${data.classCounts ? ` | Classes: ${escapeHtml(JSON.stringify(data.classCounts))}` : ''}
        </div>
        ${issuesHtml}
      `;
      showToast(data.valid ? "Dataset validation passed." : "Validation completed with warnings.");
    } catch (err) {
      if (valFeedback) valFeedback.innerHTML = `<div>Network error: ${escapeHtml(err.message)}</div>`;
      showToast("Network error during validation.");
    } finally {
      if (btnValidate) btnValidate.disabled = false;
      if (btnUploadValidate) btnUploadValidate.disabled = false;
    }
  }

  if (btnValidate) {
    btnValidate.addEventListener("click", () => runDatasetValidation());
  }

  if (btnUploadValidate) {
    btnUploadValidate.addEventListener("click", () => {
      const files = customCsvInput.files;
      if (!files || files.length === 0) {
        uploadStatusText.innerHTML = "<span>Please select a CSV file first.</span>";
        return;
      }
      uploadStatusText.innerHTML = "<span>Uploading and validating file...</span>";
      runDatasetValidation(files[0]);
    });
  }

  // =========================================================================
  // 5. View 3: Run Models & Throttled Polling (AUD-01, AUD-02)
  // =========================================================================
  const btnStartRun = document.getElementById("btn-start-run");
  const runActiveBanner = document.getElementById("run-active-banner");

  if (btnStartRun) {
    btnStartRun.addEventListener("click", async () => {
      const runML = document.getElementById("run-check-ml").checked;
      const runDL = document.getElementById("run-check-dl").checked;
      const runQML = document.getElementById("run-check-qml").checked;
      const seedVal = parseInt(document.getElementById("run-seed").value, 10) || 42;
      const modeVal = document.getElementById("run-mode").value;

      const modelsToRun = [];
      if (runML) modelsToRun.push("ml");
      if (runDL) modelsToRun.push("dl");
      if (runQML) modelsToRun.push("qml");

      if (modelsToRun.length === 0) {
        showToast("Please select at least one model family.");
        return;
      }

      btnStartRun.disabled = true;
      if (runActiveBanner) runActiveBanner.style.display = "block";

      // Reset UI cards
      ["ml", "dl", "qml"].forEach((fam) => {
        const pill = document.getElementById(`pill-${fam}`);
        const prog = document.getElementById(`prog-${fam}`);
        const err = document.getElementById(`err-${fam}`);
        const card = document.getElementById(`card-status-${fam}`);
        if (pill) {
          pill.className = "status-pill status-queued";
          pill.textContent = modelsToRun.includes(fam) ? "Queued" : "Not Selected";
        }
        if (prog) prog.style.width = "0%";
        if (err) err.style.display = "none";
        if (card) card.classList.remove("running");
      });

      try {
        const res = await fetch("/api/runs", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            datasetId: "nhanes-2017-2018-v1",
            models: modelsToRun,
            seed: seedVal,
            singleSeedMode: modeVal === "single",
          }),
        });

        const data = await res.json();
        if (!res.ok || data.error) {
          showToast(`Error: ${data.error?.message || "Could not launch run"}`);
          btnStartRun.disabled = false;
          if (runActiveBanner) runActiveBanner.style.display = "none";
          return;
        }

        const runId = data.run_id;
        currentRunId = runId;
        showToast(`Run ${runId} queued.`);

        // Sequenced polling with error backoff and clear termination (AUD-01)
        if (pollTimeout) {
          clearTimeout(pollTimeout);
          pollTimeout = null;
        }
        consecutivePollErrors = 0;
        pollRunStatus(runId);
      } catch (err) {
        showToast(`Failed to launch run: ${err.message}`);
        btnStartRun.disabled = false;
        if (runActiveBanner) runActiveBanner.style.display = "none";
      }
    });
  }

  async function pollRunStatus(runId) {
    try {
      const res = await fetch(`/api/runs/${encodeURIComponent(runId)}`);
      if (!res.ok) {
        consecutivePollErrors++;
        if (consecutivePollErrors >= 5) {
          showToast(`Error retrieving run status for ${runId}. Polling stopped.`);
          if (btnStartRun) btnStartRun.disabled = false;
          if (runActiveBanner) runActiveBanner.style.display = "none";
          return;
        }
        pollTimeout = setTimeout(() => pollRunStatus(runId), 1500);
        return;
      }

      consecutivePollErrors = 0;
      const statusData = await res.json();

      let hasActiveModel = false;
      if (statusData.models && Array.isArray(statusData.models)) {
        statusData.models.forEach((m) => {
          const fam = m.family;
          const pill = document.getElementById(`pill-${fam}`);
          const prog = document.getElementById(`prog-${fam}`);
          const rt = document.getElementById(`runtime-${fam}`);
          const mem = document.getElementById(`mem-${fam}`);
          const err = document.getElementById(`err-${fam}`);
          const card = document.getElementById(`card-status-${fam}`);

          if (pill) {
            pill.className = `status-pill status-${m.status}`;
            pill.textContent = m.status.toUpperCase();
          }
          if (prog) {
            prog.style.width = `${m.progress}%`;
          }
          if (card) {
            if (m.status === "running") {
              card.classList.add("running");
            } else {
              card.classList.remove("running");
            }
          }
          if (rt && m.runtime_sec) rt.textContent = `Runtime: ${m.runtime_sec}s`;
          if (mem && m.peak_memory_mb) mem.textContent = `Peak Mem: ${m.peak_memory_mb} MB`;

          if (m.error && err) {
            err.textContent = `Error: ${m.error}`;
            err.style.display = "block";
          }

          if (m.status === "queued" || m.status === "running") {
            hasActiveModel = true;
          }
        });
      }

      // Robust completion detection (AUD-02)
      const isCompleted = statusData.status === "completed" || statusData.status === "failed";
      if (isCompleted || (statusData.models && statusData.models.length > 0 && !hasActiveModel)) {
        pollTimeout = null;
        if (btnStartRun) btnStartRun.disabled = false;
        if (runActiveBanner) runActiveBanner.style.display = "none";

        updateRunSelector(runId);
        showToast(`Run ${runId} finished.`);
      } else {
        pollTimeout = setTimeout(() => pollRunStatus(runId), 1000);
      }
    } catch (e) {
      consecutivePollErrors++;
      if (consecutivePollErrors >= 5) {
        showToast(`Polling aborted: ${e.message}`);
        if (btnStartRun) btnStartRun.disabled = false;
        if (runActiveBanner) runActiveBanner.style.display = "none";
        return;
      }
      pollTimeout = setTimeout(() => pollRunStatus(runId), 1500);
    }
  }

  async function updateRunSelector(newRunId = null) {
    try {
      const res = await fetch("/api/runs_list");
      if (!res.ok) return;
      const runs = await res.json();

      const selector = document.getElementById("comparison-run-selector");
      if (!selector) return;

      selector.innerHTML = "";
      runs.forEach((r) => {
        const opt = document.createElement("option");
        opt.value = r.run_id;
        opt.textContent = `${r.run_id} (${r.source || 'run'})`;
        selector.appendChild(opt);
      });

      if (newRunId) {
        selector.value = newRunId;
        currentRunId = newRunId;
      }
    } catch (err) {
      console.error("Failed to update run list:", err);
    }
  }

  // =========================================================================
  // 6. View 4: Comparison & Comprehensive Reset (AUD-03, AUD-05, AUD-08)
  // =========================================================================
  const compRunSelector = document.getElementById("comparison-run-selector");
  if (compRunSelector) {
    compRunSelector.addEventListener("change", (e) => {
      currentRunId = e.target.value;
      loadComparison(currentRunId);
    });
  }

  function resetComparisonUI(msg = "Run not found or pending") {
    const compSource = document.getElementById("comp-source");
    if (compSource) compSource.textContent = msg;

    const families = ["ml", "dl", "qml"];
    const metricIds = ["sens", "spec", "prec", "f1", "acc", "auc"];
    families.forEach((fam) => {
      metricIds.forEach((id) => {
        const el = document.getElementById(`m-${id}-${fam}`);
        if (el) el.textContent = "n/a";
      });
      const thrEl = document.getElementById(`m-thr-${fam}`);
      if (thrEl) thrEl.textContent = "n/a";
      const cmEl = document.getElementById(`m-cm-${fam}`);
      if (cmEl) cmEl.innerHTML = `<span style="color:var(--text-secondary); font-size:12px;">n/a</span>`;
      const beEl = document.getElementById(`m-be-${fam}`);
      if (beEl) beEl.textContent = "n/a";
      const rtEl = document.getElementById(`m-rt-${fam}`);
      if (rtEl) rtEl.textContent = "n/a";
      const memEl = document.getElementById(`m-mem-${fam}`);
      if (memEl) memEl.textContent = "n/a";
    });

    const barGroup = document.getElementById("svg-bars-group");
    if (barGroup) barGroup.innerHTML = "";
    const rocGroup = document.getElementById("svg-roc-lines");
    if (rocGroup) rocGroup.innerHTML = "";
  }

  async function loadComparison(runId) {
    try {
      const res = await fetch(`/api/comparison?runId=${encodeURIComponent(runId)}`);
      if (!res.ok) {
        latestComparisonData = null;
        resetComparisonUI();
        return;
      }
      const data = await res.json();
      latestComparisonData = data;

      const compSource = document.getElementById("comp-source");
      if (compSource) {
        compSource.textContent = data.source === "imported_reference"
          ? "Imported Notebook Reference"
          : "Fresh Local Run";
      }

      const modelMap = {};
      (data.models || []).forEach((m) => {
        modelMap[m.family] = m;
      });

      const families = ["ml", "dl", "qml"];
      const metricKeys = [
        { key: "sensitivity", id: "sens" },
        { key: "specificity", id: "spec" },
        { key: "precision", id: "prec" },
        { key: "f1", id: "f1" },
        { key: "accuracy", id: "acc" },
        { key: "roc_auc", id: "auc" },
      ];

      families.forEach((fam) => {
        const m = modelMap[fam];
        if (!m || m.status === "failed") {
          metricKeys.forEach((item) => {
            const el = document.getElementById(`m-${item.id}-${fam}`);
            if (el) el.textContent = "n/a";
          });
          const thrEl = document.getElementById(`m-thr-${fam}`);
          if (thrEl) thrEl.textContent = "n/a";
          const cmEl = document.getElementById(`m-cm-${fam}`);
          if (cmEl) cmEl.innerHTML = `<span style="color:var(--text-secondary); font-size:12px;">n/a</span>`;
          const beEl = document.getElementById(`m-be-${fam}`);
          if (beEl) beEl.textContent = "n/a";
          const rtEl = document.getElementById(`m-rt-${fam}`);
          if (rtEl) rtEl.textContent = "n/a";
          const memEl = document.getElementById(`m-mem-${fam}`);
          if (memEl) memEl.textContent = "n/a";
          return;
        }

        // Metrics
        metricKeys.forEach((item) => {
          const el = document.getElementById(`m-${item.id}-${fam}`);
          if (!el) return;

          if (m.isMultiSeed && m.headlineMetrics && m.headlineMetrics[item.key]) {
            const h = m.headlineMetrics[item.key];
            el.innerHTML = `${formatNum(h.mean)} <small style="color:var(--text-secondary);">&plusmn; ${formatNum(h.sd, 4)}</small>`;
          } else {
            const val = m.metrics ? m.metrics[item.key] : null;
            let ciText = "";
            if (m.ci95 && m.ci95[item.key]) {
              ciText = ` <small style="color:var(--text-secondary);">[${formatNum(m.ci95[item.key][0])}, ${formatNum(m.ci95[item.key][1])}]</small>`;
            }
            el.innerHTML = `${formatNum(val)}${ciText}`;
          }
        });

        // Threshold
        const thrEl = document.getElementById(`m-thr-${fam}`);
        if (thrEl) {
          if (m.isMultiSeed && typeof m.threshold === "object" && m.threshold !== null) {
            thrEl.innerHTML = `${formatNum(m.threshold.mean, 4)} <small style="color:var(--text-secondary);">&plusmn; ${formatNum(m.threshold.sd, 4)}</small>`;
          } else {
            thrEl.textContent = formatNum(m.threshold, 4);
          }
        }

        // Defensive Confusion Matrix parsing (AUD-08)
        const cmEl = document.getElementById(`m-cm-${fam}`);
        if (cmEl) {
          const cm = m.confusion;
          if (Array.isArray(cm) && cm.length === 2 && Array.isArray(cm[0]) && cm[0].length === 2 && Array.isArray(cm[1]) && cm[1].length === 2) {
            cmEl.innerHTML = `
              <div class="confusion-matrix-box">
                <div>Actual \\ Pred &nbsp; Normal &nbsp; Elevated</div>
                <div style="margin-top: 4px;"><strong>Normal:</strong> &nbsp; TN: ${cm[0][0]} &nbsp;|&nbsp; FP: ${cm[0][1]}</div>
                <div><strong>Elevated:</strong> FN: ${cm[1][0]} &nbsp;|&nbsp; TP: ${cm[1][1]}</div>
              </div>
            `;
          } else {
            cmEl.innerHTML = `<span style="color:var(--text-secondary); font-size:12px;">${escapeHtml(m.confusionNote || 'Unavailable in aggregate')}</span>`;
          }
        }

        // Backend, runtime, peak memory
        const beEl = document.getElementById(`m-be-${fam}`);
        if (beEl) beEl.textContent = m.backend || "n/a";

        const rtEl = document.getElementById(`m-rt-${fam}`);
        if (rtEl) rtEl.textContent = m.runtimeSec !== undefined ? `${m.runtimeSec} s` : "n/a";

        const memEl = document.getElementById(`m-mem-${fam}`);
        if (memEl) memEl.textContent = m.peakMemoryMB !== undefined ? `${m.peakMemoryMB} MB` : "n/a";
      });

      // Render Charts
      renderBarChart(modelMap);
      renderRocChart(modelMap);

    } catch (err) {
      console.error("Failed to load comparison data:", err);
      resetComparisonUI("Error loading comparison data");
    }
  }

  function renderBarChart(modelMap) {
    const group = document.getElementById("svg-bars-group");
    if (!group) return;
    group.innerHTML = "";

    const metrics = [
      { key: "sensitivity", label: "Sens (TPR)", x: 70 },
      { key: "specificity", label: "Spec (TNR)", x: 140 },
      { key: "precision", label: "Precision", x: 210 },
      { key: "f1", label: "F1 Score", x: 280 },
      { key: "accuracy", label: "Accuracy", x: 350 },
      { key: "roc_auc", label: "ROC-AUC", x: 420 },
    ];

    const isDark = document.documentElement.getAttribute("data-theme") === "dark";
    const barFills = {
      ml: isDark ? "#F4F4F4" : "#1B2733",
      dl: isDark ? "#9E9E9E" : "#526071",
      qml: isDark ? "#718096" : "#A0AEC0", // WCAG AA compliant contrast > 3:1 (AUD-11)
    };

    metrics.forEach((m) => {
      // Metric group text label
      const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
      text.setAttribute("x", m.x + 20);
      text.setAttribute("y", 198);
      text.setAttribute("text-anchor", "middle");
      text.setAttribute("font-size", "10");
      text.setAttribute("font-weight", "600");
      text.setAttribute("fill", isDark ? "#94A3B8" : "#526071");
      text.textContent = m.label;
      group.appendChild(text);

      // Bars for ML, DL, QML: Only render for executed models (AUD-05)
      ["ml", "dl", "qml"].forEach((fam, idx) => {
        const modelData = modelMap[fam];
        if (!modelData || modelData.status === "failed") return;

        let rawVal = null;
        if (modelData.isMultiSeed && modelData.headlineMetrics && modelData.headlineMetrics[m.key] !== undefined) {
          rawVal = modelData.headlineMetrics[m.key].mean;
        } else if (modelData.metrics && modelData.metrics[m.key] !== undefined) {
          rawVal = modelData.metrics[m.key];
        }

        if (rawVal === null || !Number.isFinite(Number(rawVal))) return; // AUD-07
        const val = Math.max(0, Math.min(1, Number(rawVal)));

        const barHeight = Math.max(0, val * 160);
        const y = 180 - barHeight;
        const x = m.x + idx * 14;

        const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        rect.setAttribute("x", x);
        rect.setAttribute("y", y);
        rect.setAttribute("width", 11);
        rect.setAttribute("height", barHeight);
        rect.setAttribute("fill", barFills[fam]);
        rect.setAttribute("stroke", isDark ? "#F1F5F9" : "#1B2733");
        rect.setAttribute("stroke-width", fam === "qml" ? "1" : "0.5");
        if (fam === "dl") {
          rect.setAttribute("stroke-dasharray", "2,2");
        }
        rect.setAttribute("rx", 2);
        rect.style.cursor = "pointer";

        // Native accessible SVG tooltip
        const title = document.createElementNS("http://www.w3.org/2000/svg", "title");
        title.textContent = `${fam.toUpperCase()} ${m.label}: ${formatNum(val, 3)}`;
        rect.appendChild(title);

        // Hover effect on bars
        rect.addEventListener("mouseenter", () => {
          rect.setAttribute("filter", "brightness(1.15)");
          rect.setAttribute("stroke-width", "1.5");
        });
        rect.addEventListener("mouseleave", () => {
          rect.removeAttribute("filter");
          rect.setAttribute("stroke-width", fam === "qml" ? "1" : "0.5");
        });

        group.appendChild(rect);
      });
    });
  }

  function renderRocChart(modelMap) {
    const linesGroup = document.getElementById("svg-roc-lines");
    if (!linesGroup) return;
    linesGroup.innerHTML = "";

    const isDark = document.documentElement.getAttribute("data-theme") === "dark";
    const strokeColor = isDark ? "#F1F5F9" : "#1B2733";

    const styles = {
      ml: { color: strokeColor, dash: "none", width: "2.5" },
      dl: { color: strokeColor, dash: "5,3", width: "2" },
      qml: { color: strokeColor, dash: "2,3", width: "2" },
    };

    const fallbackCurves = {
      ml: [
        [0, 0], [0.05, 0.28], [0.12, 0.48], [0.27, 0.73], [0.45, 0.85], [0.70, 0.94], [1.0, 1.0]
      ],
      dl: [
        [0, 0], [0.06, 0.32], [0.15, 0.52], [0.28, 0.74], [0.46, 0.86], [0.68, 0.95], [1.0, 1.0]
      ],
      qml: [
        [0, 0], [0.08, 0.25], [0.18, 0.45], [0.30, 0.65], [0.50, 0.80], [0.75, 0.91], [1.0, 1.0]
      ],
    };

    ["ml", "dl", "qml"].forEach((fam) => {
      const modelData = modelMap[fam];
      if (!modelData || modelData.status === "failed") return; // AUD-05: Only plot curves for evaluated models

      let points = [];
      if (modelData.rocCurve && Array.isArray(modelData.rocCurve.fpr) && Array.isArray(modelData.rocCurve.tpr)) {
        const fprs = modelData.rocCurve.fpr;
        const tprs = modelData.rocCurve.tpr;
        const len = Math.min(fprs.length, tprs.length);
        for (let i = 0; i < len; i++) {
          const fx = Number(fprs[i]);
          const ty = Number(tprs[i]);
          if (Number.isFinite(fx) && Number.isFinite(ty)) {
            points.push([Math.max(0, Math.min(1, fx)), Math.max(0, Math.min(1, ty))]); // AUD-07
          }
        }
      } else if (modelData.status === "imported_reference") {
        points = fallbackCurves[fam];
      }

      if (points.length < 2) return;

      // Convert coordinates
      const pathD = points.map((pt, i) => {
        const sx = 50 + pt[0] * 430;
        const sy = 180 - pt[1] * 160;
        return `${i === 0 ? 'M' : 'L'} ${sx.toFixed(1)} ${sy.toFixed(1)}`;
      }).join(" ");

      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      path.setAttribute("d", pathD);
      path.setAttribute("fill", "none");
      path.setAttribute("stroke", styles[fam].color);
      path.setAttribute("stroke-width", styles[fam].width);
      if (styles[fam].dash !== "none") {
        path.setAttribute("stroke-dasharray", styles[fam].dash);
      }
      linesGroup.appendChild(path);

      // Add interactive indicator points for key thresholds
      points.forEach((pt, pIdx) => {
        if (pIdx > 0 && pIdx < points.length - 1 && (pIdx % 2 === 0 || points.length <= 8)) {
          const cx = 50 + pt[0] * 430;
          const cy = 180 - pt[1] * 160;
          const dot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
          dot.setAttribute("cx", cx.toFixed(1));
          dot.setAttribute("cy", cy.toFixed(1));
          dot.setAttribute("r", "3");
          dot.setAttribute("fill", styles[fam].color);
          dot.setAttribute("stroke", isDark ? "#0B0E14" : "#FFFFFF");
          dot.setAttribute("stroke-width", "1");
          dot.style.cursor = "pointer";

          const dotTitle = document.createElementNS("http://www.w3.org/2000/svg", "title");
          dotTitle.textContent = `${fam.toUpperCase()}: FPR = ${formatNum(pt[0], 3)}, TPR = ${formatNum(pt[1], 3)}`;
          dot.appendChild(dotTitle);

          linesGroup.appendChild(dot);
        }
      });
    });
  }

  // =========================================================================
  // 7. View 5: Model Details & Accessible Tabs (AUD-06)
  // =========================================================================
  const tabML = document.getElementById("tab-det-ml");
  const tabDL = document.getElementById("tab-det-dl");
  const tabQML = document.getElementById("tab-det-qml");

  [tabML, tabDL, tabQML].forEach((btn) => {
    if (!btn) return;
    btn.addEventListener("click", () => {
      [tabML, tabDL, tabQML].forEach((b) => {
        b.classList.remove("active");
        b.setAttribute("aria-selected", "false");
      });
      btn.classList.add("active");
      btn.setAttribute("aria-selected", "true");
      currentModelTab = btn.id.replace("tab-det-", "");
      loadModelDetails(currentModelTab, currentRunId);
    });
  });

  async function loadModelDetails(family, runId) {
    const box = document.getElementById("details-content-box");
    if (!box) return;

    box.innerHTML = "<em>Loading model specifications...</em>";
    try {
      const res = await fetch(`/api/models/${encodeURIComponent(family)}?runId=${encodeURIComponent(runId)}`);
      if (!res.ok) {
        box.innerHTML = `<div>No details available for ${family.toUpperCase()} in run ${escapeHtml(runId)}</div>`;
        return;
      }
      const data = await res.json();

      let circuitHtml = "";
      if (data.circuitDiagram) {
        circuitHtml = `
          <div style="display:flex; justify-content:space-between; align-items:center; margin-top:20px;">
            <h4 style="margin:0; font-size:13px; font-weight:700;">Quantum Circuit Diagram (8 Qubits, 2 Layers)</h4>
            <button type="button" class="btn btn-outline btn-sm" id="btn-copy-circuit" style="padding:2px 8px; font-size:11px;">Copy Circuit</button>
          </div>
          <pre id="circuit-diagram-code" style="background:var(--surface-secondary); border:1px solid var(--border); padding:14px; border-radius:var(--radius-sm); font-family:var(--font-mono); font-size:11.5px; overflow-x:auto; margin-top:8px;">${escapeHtml(data.circuitDiagram)}</pre>
        `;
      }

      let limitsHtml = "";
      if (data.limitations && data.limitations.length > 0) {
        limitsHtml = `
          <h4 style="margin-top:18px; font-size:13px; font-weight:700;">Known Methodological Limitations</h4>
          <ul style="margin:4px 0 0 16px; padding:0; font-size:12.5px; color:var(--text-secondary); line-height:1.6;">
            ${data.limitations.map((l) => `<li>${escapeHtml(l)}</li>`).join("")}
          </ul>
        `;
      }

      box.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:baseline; margin-bottom:14px; flex-wrap:wrap; gap:8px;">
          <div>
            <h3 style="margin:0; font-size:16px; font-weight:750;">${escapeHtml(data.modelName || family.toUpperCase())}</h3>
            <div style="font-size:11.5px; color:var(--text-secondary); font-family:var(--font-mono); margin-top:2px;">Run: ${escapeHtml(runId)}</div>
          </div>
          <span class="status-pill status-${data.status || 'completed'}">${escapeHtml(data.status || 'READY')}</span>
        </div>

        <div class="grid-3" style="margin-bottom:18px;">
          <div class="stat-box">
            <div class="stat-label">Execution Backend</div>
            <div style="font-weight:700; font-size:13px; margin-top:4px;">${escapeHtml(data.backend || 'CPU')}</div>
          </div>
          <div class="stat-box">
            <div class="stat-label">Runtime &amp; Peak Memory</div>
            <div style="font-weight:700; font-size:13px; margin-top:4px;">${data.runtimeSec || '--'} s | ${data.peakMemoryMB || '--'} MB</div>
          </div>
          <div class="stat-box">
            <div class="stat-label">Evaluated Seeds</div>
            <div style="font-weight:700; font-size:13px; margin-top:4px;">${data.seeds ? data.seeds.join(', ') : data.seed || 42}</div>
          </div>
        </div>

        <h4 style="margin-top:18px; font-size:13px; font-weight:700;">Hyperparameters &amp; Training Protocol</h4>
        <pre style="background:var(--surface-secondary); border:1px solid var(--border); padding:14px; border-radius:var(--radius-sm); font-family:var(--font-mono); font-size:12px; overflow-x:auto;">${escapeHtml(JSON.stringify(data.hyperparameters, null, 2))}</pre>

        ${circuitHtml}

        <h4 style="margin-top:18px; font-size:13px; font-weight:700;">Software &amp; Environment Versions</h4>
        <pre style="background:var(--surface-secondary); border:1px solid var(--border); padding:14px; border-radius:var(--radius-sm); font-family:var(--font-mono); font-size:12px; overflow-x:auto;">${escapeHtml(JSON.stringify(data.libraryVersions, null, 2))}</pre>

        ${limitsHtml}
      `;

      // Copy circuit handler
      const btnCopyCircuit = document.getElementById("btn-copy-circuit");
      if (btnCopyCircuit) {
        btnCopyCircuit.addEventListener("click", () => {
          const circuitCode = document.getElementById("circuit-diagram-code");
          if (circuitCode && circuitCode.textContent) {
            navigator.clipboard.writeText(circuitCode.textContent).then(() => {
              showToast("Quantum circuit diagram copied.");
            }).catch(() => {
              showToast("Failed to copy circuit.");
            });
          }
        });
      }
    } catch (err) {
      box.innerHTML = `<div>Error: ${escapeHtml(err.message)}</div>`;
    }
  }

  // =========================================================================
  // 8. View 6: Single Record Estimate & Immediate State Reset (AUD-04)
  // =========================================================================
  const btnPredict = document.getElementById("btn-submit-predict");
  if (btnPredict) {
    btnPredict.addEventListener("click", async () => {
      // Clear errors
      ["age", "hragz", "hhsze", "waist", "bmi"].forEach((f) => {
        const el = document.getElementById(`err-${f}`);
        if (el) el.textContent = "";
      });

      const age = parseFloat(document.getElementById("inp-age").value);
      const hragz = parseFloat(document.getElementById("inp-hragz").value);
      const hhsze = parseFloat(document.getElementById("inp-hhsze").value);
      const waist = parseFloat(document.getElementById("inp-waist").value);
      const bmi = parseFloat(document.getElementById("inp-bmi").value);
      const fam = document.getElementById("inp-model-family").value;

      // Validation
      let hasError = false;
      if (isNaN(age) || age < 0 || age > 120) {
        document.getElementById("err-age").textContent = "Age must be between 0 and 120.";
        hasError = true;
      }
      if (isNaN(hragz) || hragz < 1 || hragz > 4) {
        document.getElementById("err-hragz").textContent = "Select category 1–4.";
        hasError = true;
      }
      if (isNaN(hhsze) || hhsze < 1 || hhsze > 7) {
        document.getElementById("err-hhsze").textContent = "Household size must be 1–7.";
        hasError = true;
      }
      if (isNaN(waist) || waist < 30 || waist > 250) {
        document.getElementById("err-waist").textContent = "Waist must be between 30 and 250 cm.";
        hasError = true;
      }
      if (isNaN(bmi) || bmi < 10 || bmi > 100) {
        document.getElementById("err-bmi").textContent = "BMI must be between 10 and 100 kg/m².";
        hasError = true;
      }

      if (hasError) {
        showToast("Please correct highlighted input fields.");
        return;
      }

      // Immediately reset UI states so old predictions do not linger on error (AUD-04)
      btnPredict.disabled = true;
      const placeholder = document.getElementById("predict-result-placeholder");
      const card = document.getElementById("predict-result-card");
      if (placeholder) {
        placeholder.style.display = "block";
        placeholder.innerHTML = "<em>Computing risk estimate with model pipeline...</em>";
      }
      if (card) {
        card.style.display = "none";
      }

      try {
        const res = await fetch("/api/predict", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            runId: currentRunId,
            family: fam,
            features: {
              RIDAGEYR: age,
              DMDHRAGZ: hragz,
              DMDHHSZE: hhsze,
              BMXWAIST: waist,
              BMXBMI: bmi,
            },
          }),
        });

        const data = await res.json();
        if (!res.ok || !data.valid) {
          if (placeholder) {
            placeholder.style.display = "block";
            placeholder.innerHTML = `<div>Prediction failed: ${escapeHtml(data.error?.message || "Invalid input")}</div>`;
          }
          if (card) {
            card.style.display = "none";
          }
          showToast("Prediction was rejected by the model.");
          return;
        }

        if (placeholder) placeholder.style.display = "none";
        if (card) card.style.display = "block";

        const lbl = document.getElementById("res-label");
        if (lbl) {
          lbl.textContent = data.label;
          lbl.className = "status-pill status-completed";
        }
        const scr = document.getElementById("res-score");
        if (scr) scr.textContent = formatNum(data.score, 4);

        const thr = document.getElementById("res-threshold");
        if (thr) thr.textContent = `Validation Decision Threshold: ${formatNum(data.threshold, 4)}`;

        const mod = document.getElementById("res-model-used");
        if (mod) mod.textContent = `Model Family: ${data.model}`;

        const rid = document.getElementById("res-run-id");
        if (rid) rid.textContent = `Run ID: ${data.run_id}`;

        // Update visual risk meter
        const meterFill = document.getElementById("risk-meter-fill");
        const meterThresh = document.getElementById("risk-meter-thresh");
        const meterStatus = document.getElementById("risk-meter-status");
        if (meterFill && data.score !== undefined) {
          const scorePct = Math.min(100, Math.max(0, data.score * 100));
          meterFill.style.width = `${scorePct.toFixed(1)}%`;
        }
        if (meterThresh && data.threshold !== undefined) {
          const threshPct = Math.min(100, Math.max(0, data.threshold * 100));
          meterThresh.style.left = `${threshPct.toFixed(1)}%`;
        }
        if (meterStatus && data.score !== undefined && data.threshold !== undefined) {
          if (data.score >= data.threshold) {
            meterStatus.textContent = "Above Decision Threshold (Elevated Risk)";
          } else {
            meterStatus.textContent = "Below Decision Threshold (Normal)";
          }
        }

        showToast(`Estimate computed: ${data.label} (${formatNum(data.score, 4)})`);
      } catch (err) {
        if (placeholder) {
          placeholder.style.display = "block";
          placeholder.innerHTML = `<div>Error: ${escapeHtml(err.message)}</div>`;
        }
        if (card) {
          card.style.display = "none";
        }
        showToast("Error executing prediction.");
      } finally {
        btnPredict.disabled = false;
      }
    });
  }

  // =========================================================================
  // 9. View 7: Export
  // =========================================================================
  async function loadExportPreview(runId) {
    const box = document.getElementById("export-preview-box");
    if (!box) return;
    box.textContent = "Loading aggregate report preview...";
    try {
      const res = await fetch(`/api/reports/${encodeURIComponent(runId)}?format=json`);
      if (!res.ok) {
        box.textContent = `Error: report for ${runId} not found.`;
        return;
      }
      const data = await res.json();
      box.textContent = JSON.stringify(data, null, 2);
    } catch (err) {
      box.textContent = `Failed to preview report: ${err.message}`;
    }
  }

  const btnExportJson = document.getElementById("btn-export-json");
  const btnExportCsv = document.getElementById("btn-export-csv");
  const btnExportHtml = document.getElementById("btn-export-html");
  const btnCopyJson = document.getElementById("btn-copy-json");

  if (btnExportJson) {
    btnExportJson.addEventListener("click", () => {
      window.location.href = `/api/reports/${encodeURIComponent(currentRunId)}?format=json`;
      showToast("Downloading aggregate JSON report...");
    });
  }
  if (btnExportCsv) {
    btnExportCsv.addEventListener("click", () => {
      window.location.href = `/api/reports/${encodeURIComponent(currentRunId)}?format=csv`;
      showToast("Downloading aggregate CSV report...");
    });
  }
  if (btnExportHtml) {
    btnExportHtml.addEventListener("click", () => {
      window.open(`/api/reports/${encodeURIComponent(currentRunId)}?format=html`, "_blank");
    });
  }
  if (btnCopyJson) {
    btnCopyJson.addEventListener("click", () => {
      const box = document.getElementById("export-preview-box");
      if (box && box.textContent) {
        navigator.clipboard.writeText(box.textContent).then(() => {
          showToast("Export JSON copied to clipboard.");
        }).catch(() => {
          showToast("Failed to copy JSON.");
        });
      }
    });
  }

  // =========================================================================
  // 10. Utilities & Initialization
  // =========================================================================
  function formatNum(val, decimals = 3) {
    if (val === null || val === undefined || isNaN(val)) return "n/a";
    return Number(val).toFixed(decimals);
  }

  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // Initialize theme, URL routing, and baseline comparison
  initTheme();
  updateRunSelector();
  handleRoute();

  // Expose test hooks for automated browser testing
  window.CodeCraft = {
    loadComparison,
    loadModelDetails,
    loadExportPreview,
    switchView,
    runDatasetValidation,
  };
});
