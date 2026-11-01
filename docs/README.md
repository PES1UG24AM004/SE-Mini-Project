# CodeCraft Documentation Index

Welcome to the central documentation index for the **CodeCraft Early Metabolic Risk Detection Platform** (Software Engineering Mini-Project, PES University).

All project documentation has been consolidated into a structured, discoverable hierarchy adhering to professional software engineering practices and kebab-case naming conventions.

---

## 1. Documentation Taxonomy & Quick Reference

| Directory | Deliverable / File | Type | Status | Description |
| :--- | :--- | :--- | :--- | :--- |
| [`01-requirements/`](01-requirements/) | [`product-backlog.docx`](01-requirements/product-backlog.docx) | DOCX | **Active (Jira Backlog)** | 13 epics, 63 work items (23 stories, 39 tasks) mapped to SRS requirement IDs; includes proposed Fibonacci story points and team-reported statuses. |
| [`01-requirements/`](01-requirements/) | [`software-requirements-specification.pdf`](01-requirements/software-requirements-specification.pdf) | PDF | **Authoritative Baseline** | Original 31-page course submission (Part 1: SRS, SAD, and STP) dated 12 October 2026. |
| [`01-requirements/`](01-requirements/) | [`requirements-traceability-matrix.md`](01-requirements/requirements-traceability-matrix.md) | Markdown | **Verified** | Bidirectional Requirements Traceability Matrix (RTM) linking FR-01 through FR-18, NFRs, and Security Requirements to source modules and acceptance test cases. |
| [`02-architecture/`](02-architecture/) | [`software-architecture-and-design.docx`](02-architecture/software-architecture-and-design.docx) | DOCX | **Authoritative Specification** | Software Architecture and Design Specification (Part B) specifying the layered local architecture, ModelAdapter strategy pattern, data flow, and security controls. |
| [`03-sprints/`](03-sprints/) | [`sprint-1-reconstructed.docx`](03-sprints/sprint-1-reconstructed.docx) | DOCX | **Reconstructed** | Sprint 1 planning, candidate scope, review, and retrospective (19–23 October 2026); clearly labeled as reconstructed from technical epics without fabricated Jira commitments. |
| [`03-sprints/`](03-sprints/) | [`sprint-2-interim.docx`](03-sprints/sprint-2-interim.docx) | DOCX | **Interim** | Sprint 2 planning, scope changes (CODECRAFT-11 addition), burnup charts, and review (26–30 October 2026); maintained as interim pending final team sign-off. |
| [`04-testing/`](04-testing/) | [`software-test-plan.docx`](04-testing/software-test-plan.docx) | DOCX | **Authoritative Plan** | Formal IEEE-style Software Test Plan (STP-CODECRAFT-EMRD-1.0, Part C) specifying TC-01 through TC-22, pass/fail thresholds, and critical test classifications. |
| [`04-testing/`](04-testing/) | [`unit-test-report.docx`](04-testing/unit-test-report.docx) | DOCX | **Draft (Awaiting Evidence)** | Unit and component test report covering modules against STP cases (TC-01..10, TC-16, TC-20); explicitly tracks unverified/NOT RUN module tests without false claims. |
| [`04-testing/`](04-testing/) | [`system-test-report.docx`](04-testing/system-test-report.docx) | DOCX | **Illustrative Draft** | System-level test report (TC-11..15, TC-17..19, TC-21..22); includes prominent warning that Section 5 execution values are simulated examples for format verification. |
| [`05-devops/`](05-devops/) | [`devops-tool-adoption.docx`](05-devops/devops-tool-adoption.docx) | DOCX | **Authoritative Report** | DevOps tool adoption document distinguishing verified tool practices (Git, GitHub, GitHub Actions, Pytest, MLflow) from planned/reported workflows. |
| [`05-devops/`](05-devops/) | [`mlops-guide.md`](05-devops/mlops-guide.md) | Markdown | **Active Operational Guide** | Comprehensive guide covering GitHub Actions CI architecture, local/remote MLflow tracking, hierarchical runs, artifact storage, and troubleshooting. |
| [`reports/`](reports/) | [`documentation-consolidation-report.md`](reports/documentation-consolidation-report.md) | Markdown | **Final Audit Deliverable** | Master audit report detailing source inventory, SHA-256 verifications, duplicate removals, Git hygiene, and end-to-end verification. |
| [`reports/`](reports/) | [`codecraft-complete-project-audit.md`](reports/codecraft-complete-project-audit.md) | Markdown | **Technical Audit** | Comprehensive independent audit report covering architecture, data leakage verification, model evaluations, UI compliance, and security. |
| [`reports/`](reports/) | [`github-integration-report.md`](reports/github-integration-report.md) | Markdown | **Milestone Report** | Full-stack application integration and GitHub publishing verification report. |
| [`reports/`](reports/) | [`repository-completeness-audit.md`](reports/repository-completeness-audit.md) | Markdown | **Milestone Report** | Completeness verification covering source modules, dataset splits, test fixtures, notebooks, and screenshots. |
| [`reports/`](reports/) | [`mlops-integration-report.md`](reports/mlops-integration-report.md) | Markdown | **Milestone Report** | Verification report for GitHub Actions CI and MLflow experiment tracking integration. |
| [`reports/`](reports/) | [`browser-debug-report.md`](reports/browser-debug-report.md) | Markdown | **Diagnostic Report** | Chrome DevTools debug report and 25-point browser regression checklist results. |
| [`reports/`](reports/) | [`frontend-repair-notes.md`](reports/frontend-repair-notes.md) | Markdown | **Engineering Notes** | Architectural notes on single-page navigation, accessibility, and grayscale design system compliance. |
| [`reports/`](reports/) | [`automated-test-execution-report.md`](reports/automated-test-execution-report.md) | Markdown | **Execution Log** | Automated test execution report of the 22 acceptance tests (`tests/test_all_requirements.py`). |
| [`archive/`](archive/) | [`README.md`](archive/README.md) | Markdown | **Policy Document** | Archival policy and catalog of historical/superseded artifacts. |

---

## 2. Navigating the Deliverables

### Requirements & Product Scope
- For the formal requirement definitions, see the [Software Requirements Specification](01-requirements/software-requirements-specification.pdf).
- For the active 63-item backlog and Jira epics, see the [Product Backlog](01-requirements/product-backlog.docx).
- To trace any functional requirement (FR-01 to FR-18) to source code and tests, consult the [Requirements Traceability Matrix](01-requirements/requirements-traceability-matrix.md).

### Architecture & System Design
- For system component interactions, data flows, and security design, review the [Software Architecture and Design Specification](02-architecture/software-architecture-and-design.docx).

### Agile Sprints & Governance
- Sprint 1 (Reconstructed candidate scope): [Sprint 1 Documentation](03-sprints/sprint-1-reconstructed.docx).
- Sprint 2 (Interim delivery scope & burnup): [Sprint 2 Documentation](03-sprints/sprint-2-interim.docx).

### Testing & Verification
- Test case specifications (TC-01 through TC-22): [Software Test Plan](04-testing/software-test-plan.docx).
- Module-level test classification and coverage: [Unit Test Report](04-testing/unit-test-report.docx).
- End-to-end integration and environment testing: [System Test Report](04-testing/system-test-report.docx).
- Real-time automated test results: [Automated Test Execution Report](reports/automated-test-execution-report.md).

### DevOps & Continuous Integration
- Tool adoption and practice evidence: [DevOps Tool Adoption](05-devops/devops-tool-adoption.docx).
- Local MLflow server & GitHub Actions setup: [MLOps Engineering Guide](05-devops/mlops-guide.md).
