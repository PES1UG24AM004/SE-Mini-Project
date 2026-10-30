# CodeCraft: Early Metabolic Risk Detection Platform

Software Engineering Mini-Project — PES University (RR Campus)

## 📌 Project Overview
The **Early Metabolic Risk Detection** project is designed to evaluate, preprocess, and model clinical and survey health data from the **CDC NHANES 2017–2018** (National Health and Nutrition Examination Survey) to provide predictive screening and risk assessment for metabolic syndrome and diabetes.

## 👥 Contributors
- **Aarav Yuval** (PES1UG24AM004)
- **Abhay TS** (PES1UG24AM008)
- **Abhishek PH** (PES1UG24AM013)

**Instructor:** Cvsn Reddy

---

## 📁 Repository Structure
```
├── CODECRAFT_COMPLETE_PROJECT_AUDIT.md # Technical audit report & architecture verification
├── data/
│   ├── processed/                      # Merged and model-ready processed datasets
│   ├── reports/                        # Data auditing, missing value, and manifest reports
│   └── splits/                         # Train, validation, and test dataset splits
├── models/
│   └── preprocessing/                  # Preprocessing pipelines & joblib transformers
├── notebooks/
│   └── 01_dataset_loading_and_preparation.ipynb # Data pipeline, cleaning, and preparation
└── raw/                                # NHANES raw survey files (BMX_J.XPT, DEMO_J.XPT, GHB_J.XPT)
```

## 📊 Dataset & Pipeline
- **Raw Data Source**: CDC NHANES 2017–2018 Body Measures (`BMX_J`), Demographics (`DEMO_J`), and Glycohemoglobin (`GHB_J`).
- **Data Preprocessing**: Data cleaning, handling missing values, cohort filtering for adult respondents, standardization, and feature encoding.
- **Data Splits**: Leakage-free train / validation / test splits with complete split manifest and distribution logs.

---
*Refer to [CODECRAFT_COMPLETE_PROJECT_AUDIT.md](CODECRAFT_COMPLETE_PROJECT_AUDIT.md) for detailed technical specifications and audit reports.*
