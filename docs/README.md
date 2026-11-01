# CodeCraft Academic Documentation Index & 30-Mark Rubric Mapping

Welcome to the central academic documentation directory for the **CodeCraft Early Metabolic Risk Detection Platform** (Software Engineering Mini-Project, PES University).

This directory organizes all coursework deliverables according to the official **30-Mark Academic Assessment Rubric**, providing direct navigation, canonical paths, and verified academic statuses for course evaluation.

---

## 1. 30-Mark Assessment Rubric Checklist

| No. | Academic Deliverable | Marks | Canonical Location | Format | Verification Status | Deliverable Summary |
| :---: | :--- | :---: | :--- | :---: | :---: | :--- |
| 1 | **Software Requirements Specification (SRS)** | **5** | [`01-requirements/software-requirements-specification.pdf`](01-requirements/software-requirements-specification.pdf) | PDF | **VERIFIED** | Formal 31-page baseline specification (Part 1, 12 Oct 2026) detailing FR-01..18, NFRs, and Security Requirements. |
| 2 | **Software Test Plan (STP)** | **2** | [`04-testing/software-test-plan.docx`](04-testing/software-test-plan.docx) | DOCX | **VERIFIED** | IEEE-style Software Test Plan (STP-CODECRAFT-EMRD-1.0, Part C) specifying TC-01 through TC-22 and pass/fail thresholds. |
| 3 | **Software Architecture and Design (SAD)** | **3** | [`02-architecture/software-architecture-and-design.docx`](02-architecture/software-architecture-and-design.docx) | DOCX | **VERIFIED** | Formal SAD (Part B) specifying the layered architecture, ModelAdapter strategy pattern, data flow, and security controls. |
| 4 | **Product Backlog** | **4** | [`01-requirements/product-backlog.docx`](01-requirements/product-backlog.docx) | DOCX | **PRESENT WITH GAPS** | AE2 Backlog: 13 epics, 63 work items (23 stories, 39 tasks) mapped to SRS with proposed Fibonacci estimates and reported Done statuses. |
| 5 | **Sprint 1** | **3** | [`03-sprints/sprint-1-reconstructed.docx`](03-sprints/sprint-1-reconstructed.docx) | DOCX | **PRESENT WITH GAPS (RECONSTRUCTED)** | Reconstructed Sprint 1 planning and candidate scope (19–23 Oct 2026); unattributed scope preserved without fabricated Jira commitments. |
| 6 | **Sprint 2** | **3** | [`03-sprints/sprint-2-interim.docx`](03-sprints/sprint-2-interim.docx) | DOCX | **PRESENT WITH GAPS (INTERIM)** | Interim Sprint 2 scope, burnup charts, and review (26–30 Oct 2026); tracks CODECRAFT-11 addition and open questions pending sign-off. |
| 7 | **Unit Test Report** | **4** | [`04-testing/unit-test-report.docx`](04-testing/unit-test-report.docx) | DOCX | **PRESENT WITH GAPS (DRAFT)** | AE4 Unit Test Report covering module tests (TC-01..10, TC-16, TC-20); draft awaiting separate module-level execution logs. |
| 8 | **System Test Report** | **3** | [`04-testing/system-test-report.docx`](04-testing/system-test-report.docx) | DOCX | **PRESENT WITH GAPS (ILLUSTRATIVE)** | AE4 System Test Report (TC-11..15, TC-17..19, TC-21..22); includes mock execution format templates explicitly identified for replacement. |
| 9 | **DevOps Tool Adoption** | **3** | [`05-devops/devops-tool-adoption.docx`](05-devops/devops-tool-adoption.docx) | DOCX | **VERIFIED (EVIDENCED)** | AE5 DevOps Report distinguishing verified tool practices (Git, GitHub, GitHub Actions CI, Pytest, MLflow) from reported workflows. |
| | **TOTAL** | **30** | | | | **Part 1 (Items 1–3) = 10 Marks \| Part 2 (Items 4–9) = 20 Marks** |

---

## 2. Directory Hierarchy

```text
docs/
├── README.md                                      # Central 30-mark rubric index and deliverable roadmap
├── 01-requirements/                               # Requirements & Backlog (Items 1 & 4)
│   ├── software-requirements-specification.pdf    # Graded Deliverable 1: SRS (5 Marks)
│   └── product-backlog.docx                       # Graded Deliverable 4: Product Backlog (4 Marks)
├── 02-architecture/                               # Architecture & Detailed Design (Item 3)
│   └── software-architecture-and-design.docx      # Graded Deliverable 3: SAD (3 Marks)
├── 03-sprints/                                    # Agile Governance & Sprints (Items 5 & 6)
│   ├── sprint-1-reconstructed.docx                # Graded Deliverable 5: Sprint 1 Reconstructed (3 Marks)
│   └── sprint-2-interim.docx                      # Graded Deliverable 6: Sprint 2 Interim (3 Marks)
├── 04-testing/                                    # Testing Strategy & Test Reports (Items 2, 7 & 8)
│   ├── software-test-plan.docx                    # Graded Deliverable 2: STP (2 Marks)
│   ├── unit-test-report.docx                      # Graded Deliverable 7: Unit Test Report (4 Marks)
│   └── system-test-report.docx                    # Graded Deliverable 8: System Test Report (3 Marks)
├── 05-devops/                                     # DevOps Tool Adoption (Item 9)
│   └── devops-tool-adoption.docx                  # Graded Deliverable 9: DevOps Adoption Report (3 Marks)
├── technical/                                     # Supporting Technical Engineering Guides
│   ├── requirements-traceability-matrix.md        # Technical RTM mapping SRS to backend code & tests
│   └── mlops-guide.md                             # Operational engineering guide for MLflow & CI
└── reports/                                       # Repository Housekeeping & Verification
    └── documentation-consolidation-report.md      # Final audit report of repository consolidation
```

---

## 3. Supporting Technical Documentation

In addition to the graded academic deliverables, two supporting engineering guides are maintained in [`technical/`](technical/):

- [**Requirements Traceability Matrix (RTM)**](technical/requirements-traceability-matrix.md): Bidirectional matrix linking FR-01 through FR-18, NFRs, and Security Requirements directly to Python implementation files and acceptance test functions.
- [**MLOps & CI/CD Engineering Guide**](technical/mlops-guide.md): Practical technical guide covering the 5-stage GitHub Actions CI architecture, local SQLite/remote MLflow tracking, hierarchical experiment runs, and troubleshooting.

---

## 4. Academic Evidence Boundaries & Status Definitions

- **VERIFIED:** The deliverable is complete, structurally intact, and validated against the repository codebase.
- **PRESENT WITH GAPS:** The deliverable exists in the repository, but specific evidence boundaries or historical limitations are explicitly disclosed:
  - **Sprint 1 (Reconstructed):** Labeled as reconstructed candidate scope because original dated Jira sprint activities and standup logs from 19–23 October 2026 were not archived in Jira.
  - **Sprint 2 (Interim):** Documented as interim delivery scope; CODECRAFT-11 was added mid-sprint, and open review questions remain pending team confirmation.
  - **Unit Test Report (Draft):** The automated acceptance test suite executes 22 integrated acceptance tests in Pytest (`TC-01` to `TC-22`) with 100% pass rate. However, separate module-level unit tests for individual functions remain unevidenced and are accurately preserved as draft status without fabricated claims.
  - **System Test Report (Illustrative):** Section 5 contains simulated timings and browser session formats. These are clearly marked as illustrative mock format templates awaiting live measured session logs.
  - **DevOps Tool Adoption (Evidenced vs. Reported):** Distinguishes verified tool usage (Git, GitHub, GitHub Actions CI, Pytest, MLflow) from planned/reported workflow practices.
