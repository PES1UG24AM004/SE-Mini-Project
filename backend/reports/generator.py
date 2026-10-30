"""Aggregate-only report generator with comprehensive experiment provenance."""
import csv
import io
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.config import (
    DATASET_VERSION,
    NEGATIVE_CLASS,
    POSITIVE_CLASS,
    RANKING_METRIC,
    WARNING_TEXT,
)
from backend.data.validator import sanitize_cell_for_export


class ReportGenerator:
    """Generates aggregate-only research reports in JSON, CSV, and standalone HTML formats."""

    @staticmethod
    def build_aggregate_report_dict(run_record: Dict[str, Any]) -> Dict[str, Any]:
        """Constructs an aggregate-only dictionary preserving experiment provenance."""
        run_id = run_record.get("run_id", "unknown")
        test_split = run_record.get("test_split", {})

        report: Dict[str, Any] = {
            "report_version": "1.0.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "warning": WARNING_TEXT,
            "provenance": {
                "run_id": run_id,
                "source": run_record.get("source", "local_run"),
                "dataset_version": run_record.get("dataset_version", DATASET_VERSION),
                "created_at": run_record.get("created_at"),
                "split_hash": run_record.get("split_hash"),
                "split_protocol": run_record.get("split_protocol", "70/15/15 stratified split"),
                "seed": run_record.get("seed", 42),
                "ranking_metric": run_record.get("ranking_metric", RANKING_METRIC),
                "threshold_rule": run_record.get("threshold_rule"),
                "positive_class": POSITIVE_CLASS,
                "negative_class": NEGATIVE_CLASS,
                "label_definition": (
                    "Normal: HbA1c < 5.7%; Elevated Risk: 5.7% <= HbA1c < 6.5%. "
                    "Cross-sectional survey classification (NHANES 2017-2018), not a prediction of future disease."
                ),
                "test_split_context": {
                    "test_n": test_split.get("n", 678),
                    "test_prevalence": test_split.get("prevalence", 0.347),
                    "positive_count": test_split.get("positive_count", 235),
                    "negative_count": test_split.get("negative_count", 443),
                    "weighting": test_split.get("weighting", "unweighted"),
                },
                "feature_set": run_record.get("feature_set", {}),
                "forbidden_fields_excluded": [
                    "SEQN", "LBXGH", "WTINT2YR", "WTMEC2YR", "SDMVPSU", "SDMVSTRA", "identifiers"
                ],
                "missing_value_policy": "Imputed on training rows only (median numeric, mode categorical); no leakage.",
            },
            "metric_definitions": {
                "sensitivity": "True Positive Rate (Recall) = TP / (TP + FN)",
                "specificity": "True Negative Rate = TN / (TN + FP)",
                "precision": "Positive Predictive Value = TP / (TP + FP)",
                "accuracy": "Overall Accuracy = (TP + TN) / Total",
                "f1": "Harmonic mean of precision and sensitivity = 2 * (Prec * Sens) / (Prec + Sens)",
                "roc_auc": "Area Under the Receiver Operating Characteristic Curve",
            },
            "models": {},
        }

        # Format model metrics safely
        for fam, m in run_record.get("models", {}).items():
            model_summary: Dict[str, Any] = {
                "family": fam,
                "model_name": m.get("model_name"),
                "status": m.get("status"),
                "backend": m.get("backend"),
                "runtime_sec": m.get("runtime_sec"),
                "peak_memory_mb": m.get("peak_memory_mb"),
                "threshold": m.get("threshold"),
                "metrics_at_val_threshold": m.get("metrics_at_threshold"),
                "metrics_at_0.5": m.get("metrics_at_0.5"),
                "confusion_matrix": m.get("confusion"),
                "ci95_bootstrap": m.get("ci95"),
                "headline_metrics_multi_seed": m.get("headline_metrics"),
                "hyperparameters": m.get("hyperparameters"),
                "library_versions": m.get("library_versions"),
                "limitations": m.get("limitations"),
            }
            report["models"][fam] = model_summary

        return report

    @classmethod
    def generate_json_report(cls, run_record: Dict[str, Any]) -> str:
        """Serializes aggregate report dictionary to indented JSON."""
        data = cls.build_aggregate_report_dict(run_record)
        return json.dumps(data, indent=2, default=str)

    @classmethod
    def generate_csv_report(cls, run_record: Dict[str, Any]) -> str:
        """
        Generates CSV report with spreadsheet formula injection protection.
        Contains aggregate comparison metrics only.
        """
        data = cls.build_aggregate_report_dict(run_record)
        output = io.StringIO()
        writer = csv.writer(output)

        # Header metadata
        writer.writerow(["# CodeCraft Early Metabolic Risk Detection - Aggregate Comparison Report"])
        writer.writerow(["# Warning:", sanitize_cell_for_export(data["warning"])])
        writer.writerow(["# Run ID:", sanitize_cell_for_export(data["provenance"]["run_id"])])
        writer.writerow(["# Dataset Version:", sanitize_cell_for_export(data["provenance"]["dataset_version"])])
        writer.writerow(["# Generated At:", sanitize_cell_for_export(data["generated_at"])])
        writer.writerow(["# Test Split N:", data["provenance"]["test_split_context"]["test_n"]])
        writer.writerow(["# Test Prevalence:", data["provenance"]["test_split_context"]["test_prevalence"]])
        writer.writerow(["# Ranking Metric:", sanitize_cell_for_export(data["provenance"]["ranking_metric"])])
        writer.writerow([])

        # Table header
        writer.writerow([
            "Model Family",
            "Model Name",
            "Status",
            "Backend",
            "Runtime (s)",
            "Peak Memory (MB)",
            "Threshold",
            "Sensitivity",
            "Specificity",
            "Precision",
            "F1",
            "Accuracy",
            "ROC-AUC",
            "Confusion [TN, FP, FN, TP]",
        ])

        for fam, m in data["models"].items():
            thr_val = m.get("threshold")
            if isinstance(thr_val, dict):
                thr_str = f"{thr_val.get('mean', 'n/a')} +/- {thr_val.get('sd', 0.0)}"
            else:
                thr_str = str(thr_val) if thr_val is not None else "n/a"

            # Metrics
            met = m.get("metrics_at_val_threshold") or {}
            cm = m.get("confusion_matrix")
            if cm:
                cm_str = f"TN:{cm[0][0]}, FP:{cm[0][1]}, FN:{cm[1][0]}, TP:{cm[1][1]}"
            else:
                cm_str = "Unavailable in aggregate"

            def fmt(k: str) -> str:
                # Check multi-seed headline first
                if m.get("headline_metrics_multi_seed") and k in m["headline_metrics_multi_seed"]:
                    h = m["headline_metrics_multi_seed"][k]
                    return f"{h.get('mean', 'n/a')} +/- {h.get('sd', 0.0)}"
                v = met.get(k)
                return f"{v:.4f}" if isinstance(v, (int, float)) else "n/a"

            writer.writerow([
                sanitize_cell_for_export(fam.upper()),
                sanitize_cell_for_export(m.get("model_name", "n/a")),
                sanitize_cell_for_export(m.get("status", "n/a")),
                sanitize_cell_for_export(m.get("backend", "n/a")),
                m.get("runtime_sec", "n/a"),
                m.get("peak_memory_mb", "n/a"),
                sanitize_cell_for_export(thr_str),
                sanitize_cell_for_export(fmt("sensitivity")),
                sanitize_cell_for_export(fmt("specificity")),
                sanitize_cell_for_export(fmt("precision")),
                sanitize_cell_for_export(fmt("f1")),
                sanitize_cell_for_export(fmt("accuracy")),
                sanitize_cell_for_export(fmt("roc_auc")),
                sanitize_cell_for_export(cm_str),
            ])

        return output.getvalue()

    @classmethod
    def generate_html_report(cls, run_record: Dict[str, Any]) -> str:
        """Generates a standalone, styled HTML report with the scientific lab design system."""
        data = cls.build_aggregate_report_dict(run_record)
        prov = data["provenance"]
        models = data["models"]

        def fmt_metric(m: Dict[str, Any], key: str) -> str:
            if m.get("headline_metrics_multi_seed") and key in m["headline_metrics_multi_seed"]:
                h = m["headline_metrics_multi_seed"][key]
                return f"{h.get('mean', 'n/a')} &plusmn; {h.get('sd', 0.0)}"
            v = (m.get("metrics_at_val_threshold") or {}).get(key)
            return f"{v:.4f}" if isinstance(v, (int, float)) else "n/a"

        rows_html = ""
        for fam, m in models.items():
            fam_color = {"ml": "#2C6E8F", "dl": "#478275", "qml": "#B57434"}.get(fam, "#1B2733")
            thr_val = m.get("threshold")
            if isinstance(thr_val, dict):
                thr_str = f"{thr_val.get('mean', 'n/a')} &plusmn; {thr_val.get('sd', 0.0)}"
            else:
                thr_str = f"{thr_val:.4f}" if isinstance(thr_val, (int, float)) else "n/a"

            cm = m.get("confusion_matrix")
            if cm:
                cm_html = f"TN: {cm[0][0]} | FP: {cm[0][1]}<br>FN: {cm[1][0]} | TP: {cm[1][1]}"
            else:
                cm_html = "<span style='color: #677482;'>Unavailable in imported result</span>"

            rows_html += f"""
            <tr>
              <td><strong style="color: {fam_color};">{fam.upper()}</strong><br><small>{m.get('model_name', '')}</small></td>
              <td>{m.get('backend', 'n/a')}</td>
              <td>{thr_str}</td>
              <td><strong>{fmt_metric(m, 'sensitivity')}</strong></td>
              <td>{fmt_metric(m, 'specificity')}</td>
              <td>{fmt_metric(m, 'precision')}</td>
              <td>{fmt_metric(m, 'f1')}</td>
              <td>{fmt_metric(m, 'accuracy')}</td>
              <td>{fmt_metric(m, 'roc_auc')}</td>
              <td>{cm_html}</td>
              <td>{m.get('runtime_sec', 'n/a')}s<br><small>{m.get('peak_memory_mb', 'n/a')} MB</small></td>
            </tr>
            """

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>CodeCraft - Aggregate Experiment Report ({prov['run_id']})</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: #F5F7F9;
      color: #1B2733;
      margin: 0;
      padding: 32px;
      line-height: 1.5;
    }}
    .container {{
      max-width: 1100px;
      margin: 0 auto;
      background: #FFFFFF;
      border: 1px solid #D1D8DF;
      border-radius: 6px;
      padding: 32px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }}
    .disclaimer-banner {{
      background: #FFF3CD;
      border-left: 4px solid #856404;
      padding: 12px 16px;
      margin-bottom: 24px;
      color: #856404;
      font-weight: 500;
    }}
    h1, h2, h3 {{ color: #1B2733; margin-top: 0; }}
    .meta-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
      background: #F9FAFB;
      padding: 16px;
      border-radius: 4px;
      border: 1px solid #E5E9EC;
    }}
    .meta-item {{ font-size: 13px; }}
    .meta-label {{ color: #677482; font-weight: 600; text-transform: uppercase; font-size: 11px; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 16px;
      margin-bottom: 24px;
      font-size: 13px;
    }}
    th, td {{
      padding: 10px 12px;
      text-align: left;
      border-bottom: 1px solid #E5E9EC;
    }}
    th {{
      background: #F5F7F9;
      color: #1B2733;
      font-weight: 600;
      border-top: 1px solid #D1D8DF;
      border-bottom: 2px solid #D1D8DF;
    }}
    .notes-box {{
      background: #F9FAFB;
      border: 1px solid #E5E9EC;
      padding: 16px;
      border-radius: 4px;
      font-size: 13px;
      color: #4A5568;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="disclaimer-banner">
      {WARNING_TEXT} Classification within NHANES cross-sectional survey cycle, not forecasting future disease incidence.
    </div>

    <h1>CodeCraft Early Metabolic Risk Detection</h1>
    <p style="color: #677482; margin-top: -8px;">Aggregate Experiment & Model Comparison Report | Run ID: <code>{prov['run_id']}</code></p>

    <div class="meta-grid">
      <div class="meta-item"><div class="meta-label">Dataset Version</div>{prov['dataset_version']}</div>
      <div class="meta-item"><div class="meta-label">Split Protocol</div>{prov['split_protocol']}</div>
      <div class="meta-item"><div class="meta-label">Test Split Size (N)</div>{prov['test_split_context']['test_n']} (Prevalence: {prov['test_split_context']['test_prevalence']})</div>
      <div class="meta-item"><div class="meta-label">Split Hash (SHA-256)</div><small style="word-break: break-all;">{prov['split_hash']}</small></div>
      <div class="meta-item"><div class="meta-label">Ranking Metric</div>{prov['ranking_metric']}</div>
      <div class="meta-item"><div class="meta-label">Feature Set Dimension</div>{prov['feature_set'].get('transformed_dimension', 8)} transformed columns (5 raw features)</div>
    </div>

    <h2>Test Set Model Performance (Held-out Split, Unweighted)</h2>
    <table>
      <thead>
        <tr>
          <th>Model Family</th>
          <th>Backend</th>
          <th>Threshold</th>
          <th>Sensitivity</th>
          <th>Specificity</th>
          <th>Precision</th>
          <th>F1</th>
          <th>Accuracy</th>
          <th>ROC-AUC</th>
          <th>Confusion Matrix</th>
          <th>Runtime</th>
        </tr>
      </thead>
      <tbody>
        {rows_html}
      </tbody>
    </table>

    <div class="notes-box">
      <h3 style="margin-top: 0; font-size: 14px;">Methodological Notes & Provenance</h3>
      <ul>
        <li><strong>Primary Ranking Metric:</strong> Sensitivity at validation-chosen threshold (target specificity &ge; 0.70). ROC-AUC breaks ties.</li>
        <li><strong>Multi-seed DL/QML Headline:</strong> Mean &plusmn; Standard Deviation reflects seed variation across 5 runs on a fixed split; it is not a confidence interval for generalization.</li>
        <li><strong>QML Backend:</strong> Simulated using PennyLane <code>default.qubit</code> on classical CPU. No quantum hardware used; no quantum speedup claimed.</li>
        <li><strong>Privacy Compliance:</strong> Aggregate results only. No participant identifiers (such as SEQN) or raw rows are ever exported.</li>
      </ul>
    </div>
  </div>
</body>
</html>"""
        return html
