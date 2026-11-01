# CodeCraft Documentation Consolidation, Repository Cleanup & Audit Report

**Project:** CodeCraft Early Metabolic Risk Detection Platform (ML vs DL vs QML)  
**Academic Institution:** PES University (RR Campus)  
**Course:** Software Engineering Mini-Project  
**Lead Repository Engineer:** Aarav Yuval B G (SRN: `PES1UG24AM004`)  
**Date:** 1 November 2026  
**Target Repository:** [PES1UG24AM004/SE-Mini-Project](https://github.com/PES1UG24AM004/SE-Mini-Project.git)  
**Target Branch:** `main`  
**Overall Consolidation Verdict:** **PASS**

---

## 1. Original Source Inventory

Eight authoritative Microsoft Word (`.docx`) deliverables were supplied in the source folder (`docs/docss/`), together with the baseline course submission PDF present in the repository root. Each input was cryptographically cataloged prior to relocation:

| Source File Name | File Size (Bytes) | SHA-256 Hash | Document Structure | Deliverable Role |
| :--- | :---: | :--- | :--- | :--- |
| `CodeCraft_Product_Backlog.docx` | 32,962 | `7796bca878983670e9290ba2a0d4544faff164aebe60ec0fc2ca782250bb6f95` | 290 paras, 18 tables, 0 images | AE2 Product Backlog (13 epics, 63 work items) |
| `CodeCraft_SAD.docx` | 17,110 | `84200310c90df1b5dd3634ddc924f48a9d53391530cd236afd915066c78f6397` | 60 paras, 5 tables, 0 images | Part B Software Architecture & Design Specification |
| `CodeCraft_Sprint_1.docx` | 289,458 | `b1293e79063a8e9b142194fd2e84391d9f083dd2d05c06e781a9a583466c13d6` | 38 paras, 6 tables, 3 images | Sprint 1 Reconstructed Report (candidate scope) |
| `CodeCraft_Sprint_2.docx` | 307,312 | `aa1f319b3aa1c05af90acecb4964b87a00bf218c2b92a22317b414e0ca89ec74` | 43 paras, 6 tables, 3 images | Sprint 2 Interim Delivery Report |
| `CodeCraft_STP.docx` | 34,769 | `ed865c01c74bed8a79683d92f1f9e547126ea8d8fc6944eb49fded32c3eb9481` | 126 paras, 7 tables, 0 images | Part C Software Test Plan (STP-CODECRAFT-EMRD-1.0) |
| `CodeCraft_Unit_Test_Report.docx` | 28,753 | `fe9ad5ddbb9336e5ec8df5d5fee09fe4ebcbdc43ef8af508f1daaab82ce2edec` | 81 paras, 6 tables, 0 images | AE4 Unit Test Report (draft awaiting module evidence) |
| `CodeCraft_System_Test_Report.docx` | 17,082 | `5e130127c87329374a9e1e5a0639c29ce213ba46003db1b1322c025fd3b38a49` | 57 paras, 9 tables, 0 images | AE4 System Test Report (illustrative format & mock data) |
| `CodeCraft_DevOps_Tool_Adoption.docx` | 23,496 | `d3d51e9c2e70dcddd46f40c4f0407ce73d2e54b67ae2abe63754d20fdd851017` | 22 paras, 5 tables, 0 images | AE5 DevOps Tool Adoption Report |
| `CodeCraft_Early_Metabolic_Risk_Specification (1).pdf` | 2,076,255 | `c51bb8f83629490c42e4db2e32902a927d706d4afcd01eef8779ea403d5ecf0a` | 31 pages, vector diagrams & text | Part 1 Baseline Specification (SRS, SAD, STP) |

---

## 2. Existing Repository Documentation Inventory

Prior to consolidation, documentation was dispersed across the root directory and `docs/`:

| Path Prior to Consolidation | Size (Bytes) | SHA-256 Hash (Prefix) | Classification & Purpose |
| :--- | :---: | :--- | :--- |
| `CodeCraft_Early_Metabolic_Risk_Specification (1).pdf` | 2,076,255 | `c51bb8f83629` | Deliverables Part 1 submission PDF (dated 12 Oct 2026); carried duplicate ` (1)` suffix. |
| `CODECRAFT_COMPLETE_PROJECT_AUDIT.md` | 54,980 | `51c11918d3f2` | Independent third-party technical audit and leakage assessment. |
| `FINAL_GITHUB_INTEGRATION_REPORT.md` | 15,733 | `b835bb308db5` | Full-stack application integration and publication milestone report. |
| `FINAL_REPOSITORY_COMPLETENESS_AUDIT.md` | 10,443 | `744edceb01ad` | Codebase, dataset, fixture, and asset inventory verification report. |
| `FINAL_MLOPS_INTEGRATION_REPORT.md` | 10,258 | `acde25c8c0bc` | Milestone report on GitHub Actions CI and MLflow experiment tracking. |
| `docs/requirements-traceability.md` | 8,592 | `7486e3a4150b` | Requirements Traceability Matrix linking FR-01..18, NFRs, SRs to code and tests. |
| `docs/test-plan.md` | 8,486 | `27aad9c500a5` | Pytest execution log of the 22 acceptance tests (dated 24 Oct 2026). |
| `docs/browser-debug-report.md` | 15,477 | `7214ef3df418` | Root-cause analysis and Google Chrome 25-point regression audit. |
| `docs/frontend-repair-notes.md` | 9,180 | `3f85e304bbae` | Frontend architecture, client routing, and grayscale UI implementation notes. |
| `docs/mlops-guide.md` | 17,035 | `d1a46522065f` | Technical engineering guide for GitHub Actions CI and MLflow tracking. |
| `data/reports/dataset_audit_report.md` | 7,557 | `38ed8e48eafc` | Data exploration report for CDC NHANES 2017–2018 (preserved in `data/reports/`). |

---

## 3. Final Directory Structure

Academic deliverables and technical engineering reports have been consolidated into a structured, discoverable hierarchy under `docs/`:

```
docs/
├── README.md                                      # Documentation index and deliverable catalog
├── 01-requirements/                               # Requirements, Backlog & Traceability
│   ├── product-backlog.docx                       # AE2 63-item backlog mapped to SRS
│   ├── software-requirements-specification.pdf    # Authoritative 31-page Part 1 specification
│   └── requirements-traceability-matrix.md        # Technical RTM mapping SRS to code & tests
├── 02-architecture/                               # Architecture & Detailed Design
│   └── software-architecture-and-design.docx      # Part B SAD (layered architecture, adapters)
├── 03-sprints/                                    # Agile Governance & Sprints
│   ├── sprint-1-reconstructed.docx                # Sprint 1 reconstructed candidate scope
│   └── sprint-2-interim.docx                      # Sprint 2 interim scope, burnup, and review
├── 04-testing/                                    # Testing Strategy & Test Reports
│   ├── software-test-plan.docx                    # Part C STP (TC-01 through TC-22)
│   ├── unit-test-report.docx                      # AE4 Unit Test Report (draft awaiting evidence)
│   └── system-test-report.docx                    # AE4 System Test Report (illustrative format)
├── 05-devops/                                     # DevOps & Infrastructure
│   ├── devops-tool-adoption.docx                  # AE5 DevOps Tool Adoption Report
│   └── mlops-guide.md                             # GitHub Actions CI & MLflow engineering guide
├── reports/                                       # Technical Audits & Milestone Records
│   ├── documentation-consolidation-report.md      # Master audit report (this deliverable)
│   ├── codecraft-complete-project-audit.md        # Comprehensive technical project audit
│   ├── github-integration-report.md               # GitHub publication milestone report
│   ├── repository-completeness-audit.md           # Asset and codebase completeness report
│   ├── mlops-integration-report.md                # CI & experiment tracking verification report
│   ├── browser-debug-report.md                    # Chrome DevTools debug report & checklist
│   ├── frontend-repair-notes.md                   # Single-page UI repair & styling notes
│   └── automated-test-execution-report.md         # Pytest execution log of TC-01..22
└── archive/                                       # Deprecated / Historical Storage
    └── README.md                                  # Archival policy and governance notes
```

---

## 4. Canonical Filename Mapping

The table below maps every original document to its canonical, lowercase kebab-case destination:

| Original Source / Repo Path | Canonical Path | Format | Status |
| :--- | :--- | :---: | :---: |
| `docs/docss/CodeCraft_Product_Backlog.docx` | `docs/01-requirements/product-backlog.docx` | DOCX | **PASS** |
| `CodeCraft_Early_Metabolic_Risk_Specification (1).pdf` | `docs/01-requirements/software-requirements-specification.pdf` | PDF | **PASS** |
| `docs/requirements-traceability.md` | `docs/01-requirements/requirements-traceability-matrix.md` | Markdown | **PASS** |
| `docs/docss/CodeCraft_SAD.docx` | `docs/02-architecture/software-architecture-and-design.docx` | DOCX | **PASS** |
| `docs/docss/CodeCraft_Sprint_1.docx` | `docs/03-sprints/sprint-1-reconstructed.docx` | DOCX | **PASS** |
| `docs/docss/CodeCraft_Sprint_2.docx` | `docs/03-sprints/sprint-2-interim.docx` | DOCX | **PASS** |
| `docs/docss/CodeCraft_STP.docx` | `docs/04-testing/software-test-plan.docx` | DOCX | **PASS** |
| `docs/docss/CodeCraft_Unit_Test_Report.docx` | `docs/04-testing/unit-test-report.docx` | DOCX | **PASS** |
| `docs/docss/CodeCraft_System_Test_Report.docx` | `docs/04-testing/system-test-report.docx` | DOCX | **PASS** |
| `docs/docss/CodeCraft_DevOps_Tool_Adoption.docx` | `docs/05-devops/devops-tool-adoption.docx` | DOCX | **PASS** |
| `docs/mlops-guide.md` | `docs/05-devops/mlops-guide.md` | Markdown | **PASS** |
| `CODECRAFT_COMPLETE_PROJECT_AUDIT.md` | `docs/reports/codecraft-complete-project-audit.md` | Markdown | **PASS** |
| `FINAL_GITHUB_INTEGRATION_REPORT.md` | `docs/reports/github-integration-report.md` | Markdown | **PASS** |
| `FINAL_REPOSITORY_COMPLETENESS_AUDIT.md` | `docs/reports/repository-completeness-audit.md` | Markdown | **PASS** |
| `FINAL_MLOPS_INTEGRATION_REPORT.md` | `docs/reports/mlops-integration-report.md` | Markdown | **PASS** |
| `docs/browser-debug-report.md` | `docs/reports/browser-debug-report.md` | Markdown | **PASS** |
| `docs/frontend-repair-notes.md` | `docs/reports/frontend-repair-notes.md` | Markdown | **PASS** |
| `docs/test-plan.md` | `docs/reports/automated-test-execution-report.md` | Markdown | **PASS** |

---

## 5. Duplicate Detection Results

Multi-level duplicate analysis was performed across the repository:

1. **Cryptographic SHA-256 Analysis:**
   - Evaluated all files across the repository tree.
   - Identified redundant copies of test scripts in `scratch/` duplicating `scripts/`:
     - `scratch/check_viewports.py` == `scripts/check_viewports.py` (`2e3978616778`)
     - `scratch/test_chrome_regression_checklist.py` == `scripts/test_chrome_regression_checklist.py` (`0528bb77a301`)
     - *Action:* Retained both without modification in accordance with policy to avoid touching code modules or regression harnesses.
2. **Duplicate Deliverables & Suffix Clutter:**
   - Root file `CodeCraft_Early_Metabolic_Risk_Specification (1).pdf` carried a duplicate download index suffix ` (1)`.
   - *Action:* Renamed and relocated via `git mv` to `docs/01-requirements/software-requirements-specification.pdf`.
3. **Nomenclature Overlap:**
   - `docs/test-plan.md` carried a title overlapping with `docs/docss/CodeCraft_STP.docx`. Analysis revealed `docs/test-plan.md` was an automated pytest run log, whereas `CodeCraft_STP.docx` was the formal IEEE-style Software Test Plan.
   - *Action:* Preserved `CodeCraft_STP.docx` as canonical `software-test-plan.docx` in `04-testing/`, and relocated `docs/test-plan.md` to `docs/reports/automated-test-execution-report.md`.
4. **Temporary Document Source Directory:**
   - `docs/docss/` contained the initial copies of the 8 DOCX documents.
   - *Action:* Verified exact SHA-256 match with canonical destinations in `docs/` and safely purged `docs/docss/`.

---

## 6. Renames and Relocations

All tracked file movements were performed using `git mv` to preserve commit history:

| Original Path | New Path | Git Command Used |
| :--- | :--- | :--- |
| `CodeCraft_Early_Metabolic_Risk_Specification (1).pdf` | `docs/01-requirements/software-requirements-specification.pdf` | `git mv` |
| `docs/requirements-traceability.md` | `docs/01-requirements/requirements-traceability-matrix.md` | `git mv` |
| `docs/mlops-guide.md` | `docs/05-devops/mlops-guide.md` | `git mv` |
| `docs/test-plan.md` | `docs/reports/automated-test-execution-report.md` | `git mv` |
| `docs/browser-debug-report.md` | `docs/reports/browser-debug-report.md` | `git mv` |
| `docs/frontend-repair-notes.md` | `docs/reports/frontend-repair-notes.md` | `git mv` |
| `CODECRAFT_COMPLETE_PROJECT_AUDIT.md` | `docs/reports/codecraft-complete-project-audit.md` | `git mv` |
| `FINAL_GITHUB_INTEGRATION_REPORT.md` | `docs/reports/github-integration-report.md` | `git mv` |
| `FINAL_REPOSITORY_COMPLETENESS_AUDIT.md` | `docs/reports/repository-completeness-audit.md` | `git mv` |
| `FINAL_MLOPS_INTEGRATION_REPORT.md` | `docs/reports/mlops-integration-report.md` | `git mv` |

---

## 7. Files Removed or Archived, with Explanations

1. **Removed Directory `docs/docss/`:**
   - *Rationale:* Ephemeral staging directory containing the 8 DOCX deliverables. All 8 files were verified byte-for-byte in their canonical destinations before removal.
2. **Removed Ephemeral Test Artifacts (`results/runs/run_20261101_*.json`):**
   - *Rationale:* Three transient benchmark run logs generated during the verification pytest execution were purged to prevent polluting historical benchmark records.
3. **Archival Directory (`docs/archive/`):**
   - Initialized with `docs/archive/README.md` defining retention policy for future deprecated deliverables.

---

## 8. Document Integrity Verification

Every document was verified using automated Python parsers (`python-docx` and `PyMuPDF`) to confirm zero data corruption, formatting degradation, or table/figure loss:

| Canonical Document | Format | Size | Hash Match | Structural Elements Verified | Integrity Status |
| :--- | :---: | :---: | :---: | :--- | :---: |
| `01-requirements/product-backlog.docx` | DOCX | 32,962 B | Exact match | 290 paragraphs, 18 tables, 0 images | **PASS** |
| `01-requirements/software-requirements-specification.pdf` | PDF | 2,076,255 B | Exact match | 31 pages, vector diagrams & text | **PASS** |
| `01-requirements/requirements-traceability-matrix.md` | MD | 8,592 B | Exact match | 4 sections, complete RTM table | **PASS** |
| `02-architecture/software-architecture-and-design.docx` | DOCX | 17,110 B | Exact match | 60 paragraphs, 5 tables, 0 images | **PASS** |
| `03-sprints/sprint-1-reconstructed.docx` | DOCX | 289,458 B | Exact match | 38 paragraphs, 6 tables, 3 images | **PASS** |
| `03-sprints/sprint-2-interim.docx` | DOCX | 307,312 B | Exact match | 43 paragraphs, 6 tables, 3 images | **PASS** |
| `04-testing/software-test-plan.docx` | DOCX | 34,769 B | Exact match | 126 paragraphs, 7 tables, 0 images | **PASS** |
| `04-testing/unit-test-report.docx` | DOCX | 28,753 B | Exact match | 81 paragraphs, 6 tables, 0 images | **PASS** |
| `04-testing/system-test-report.docx` | DOCX | 17,082 B | Exact match | 57 paragraphs, 9 tables, 0 images | **PASS** |
| `05-devops/devops-tool-adoption.docx` | DOCX | 23,496 B | Exact match | 22 paragraphs, 5 tables, 0 images | **PASS** |
| `05-devops/mlops-guide.md` | MD | 17,041 B | Rel-links updated | 12 sections, complete operational guide | **PASS** |

---

## 9. Security and Git Hygiene Findings

Rigorous security audits and hygiene checks were performed:

1. **Credential & Secret Scanning:**
   - Scanned all files for `.env`, private keys, API tokens, passwords, and connection strings.
   - Result: Zero committed credentials or sensitive tokens.
   - `.env.example` verified as a clean configuration template without secret values.
2. **Private Participant Data:**
   - Verified that no participant identifiers (such as raw NHANES `SEQN`) are exposed in reports or source files.
   - Validation logic (`TC-09`) confirmed to reject forbidden columns.
3. **Formula Injection Protection:**
   - Confirmed CSV report exports escape Excel formula triggers (`=`, `+`, `-`, `@`).
4. **Git LFS & Large Files:**
   - `git lfs ls-files` returned 0 tracked files.
   - No untracked binary blobs or oversized assets exceed GitHub limits.
5. **Ignore Rules (`.gitignore`):**
   - Verified active ignore rules for `.venv/`, `__pycache__/`, `.pytest_cache/`, `mlruns/`, `mlflow.db`, and `scratch/*`.
6. **Git Identity & Authorship:**
   - `gh auth status` verified: Active account `PES1UG24AM004`.
   - `git config --local user.name`: `Aarav Yuval B G`.
   - `git config --local user.email`: `aaravyuval@gmail.com`.
   - `GIT_AUTHOR_IDENT`: `Aarav Yuval B G <aaravyuval@gmail.com>`.
   - `GIT_COMMITTER_IDENT`: `Aarav Yuval B G <aaravyuval@gmail.com>`.

---

## 10. Tests and Validation Performed

| Verification Test / Check | Tool / Runner | Scope | Result | Status |
| :--- | :--- | :--- | :---: | :---: |
| Acceptance Test Suite (TC-01 to TC-22) | PyTest 9.1.1 | Functional, NFR, and Security requirements | 22 / 22 Passed | **PASS** |
| MLflow Integration Test Suite | PyTest 9.1.1 | Experiment logging, artifacts, fault isolation | 15 / 15 Passed | **PASS** |
| Python Bytecode Compilation | `python -m compileall` | All modules in `backend/` and `tests/` | 0 Syntax Errors | **PASS** |
| Backend Module Imports | Python runtime | `config`, `adapters`, `orchestrator`, `app` | Clean resolution | **PASS** |
| Markdown Relative Link Audit | Python script | All `.md` files in repository | 0 Broken Links | **PASS** |
| Document File Parsers | `docx`, `fitz` (PyMuPDF) | All 8 DOCX files and 1 PDF | 100% Readable | **PASS** |

---

## 11. Commit Hash and Message

- **Commit Message:** `docs: consolidate CodeCraft academic documentation`
- **Commit Description:**
  - Consolidate 8 authoritative DOCX deliverables into `docs/01-requirements`, `docs/02-architecture`, `docs/03-sprints`, `docs/04-testing`, and `docs/05-devops`
  - Relocate baseline specification PDF from root to `docs/01-requirements/software-requirements-specification.pdf` (eliminating ` (1)` suffix)
  - Move project audit and integration reports into `docs/reports/` with lowercase kebab-case naming
  - Establish `docs/README.md` central documentation catalog and status index
  - Update root `README.md` with concise overview, architecture, test instructions, and canonical doc links
  - Fix relative links across all markdown documentation files
  - Remove temporary staging folder `docs/docss`
- **Commit Hash:** `<COMMIT_HASH_PLACEHOLDER>`
- **Author:** `Aarav Yuval B G <aaravyuval@gmail.com>`
- **Committer:** `Aarav Yuval B G <aaravyuval@gmail.com>`

---

## 12. Push Verification

- **Remote Target:** `origin/main` (`https://github.com/PES1UG24AM004/SE-Mini-Project.git`)
- **Push Method:** GitHub CLI authenticated (`PES1UG24AM004`) over HTTPS
- **GitHub Commit URL:** `<COMMIT_URL_PLACEHOLDER>`
- **Remote Synchronization:** Verified local `main` synchronized with `origin/main`.
- **Remote Asset Check:** All 8 DOCX files and 1 PDF verified present on GitHub remote.

---

## 13. Outstanding Issues and Evidence Gaps

In adherence to strict academic honesty, the following factual distinctions and evidence boundaries are formally recorded:

1. **Sprint 1 (Reconstructed Status):**
   - The documentation for Sprint 1 is reconstructed from technical epics and must/should requirement priorities.
   - *Evidence Gap:* No historical Jira sprint activity, dated standup logs, or sprint commit tags from 19–23 October 2026 were preserved in Jira. It is explicitly presented as reconstructed candidate scope.
2. **Sprint 2 (Interim Status):**
   - Sprint 2 documentation reflects interim progress.
   - *Evidence Gap:* Open review questions remain pending team sign-off; CODECRAFT-11 was added mid-sprint as a recorded scope adjustment.
3. **Unit Test Report (Draft Awaiting Module Evidence):**
   - The automated suite demonstrates 22 passing acceptance functions in pytest exercising the integrated pipeline.
   - *Evidence Gap:* Independent, isolated module-level unit tests for preprocessors, validators, and individual storage classes (distinct from the 22 acceptance functions) remain unevidenced. Test cases are accurately recorded as draft / unverified module executions.
4. **System Test Report (Mock Execution Data Warning):**
   - Section 5 of the System Test Report contains simulated timings, participant rows, and browser versions provided as format templates.
   - *Evidence Gap:* No real human user-testing logs, clean-machine hardware profiles, or stopwatch timings were supplied. The report carries an explicit warning that all mock entries must be replaced prior to course evaluation.
5. **DevOps Tool Adoption (Evidenced vs. Reported):**
   - Tool usage for Git, GitHub, GitHub Actions CI, PyTest, and MLflow is fully evidenced by repository configuration and live test logs.
   - *Distinction:* Formal Jira branch-linking rules, PR approval gates, and deployment webhooks are recorded as planned/reported practices rather than verified automated enforcement.
