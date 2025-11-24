

# CVEye 🔍🛡️

### *A Machine Learning Lens on Exploitable Vulnerabilities*

CVEye is a predictive analytics platform that evaluates the real-world exploitation risk of known vulnerabilities (CVEs). By combining data from the **NVD**, **CISA KEV**, and **EPSS**, CVEye predicts whether a vulnerability is likely to be exploited in the wild—helping security teams prioritize remediation with confidence.

---

## 🏗️ Architecture Overview

CVEye is built on a two-stage system:

### **1. ML Pipeline**

* Ingests raw vulnerability and exploitation data
* Processes and engineers features using **BigQuery** and **Pandas**
* Trains a predictive model
* Serializes the model to `.pkl`

### **2. API Service**

* A **FastAPI** application running on **Google Cloud Run**
* Loads the trained model for real-time predictions
* Exposes an HTTP API for external integration

---

## 🚀 Step 1: Environment Setup

Clone the repository and install dependencies.

```bash
# Clone the repo
git clone https://github.com/your-username/Project_CVE.git
cd Project_CVE

# Create and activate virtual environment
python -m venv venv
source ./venv/bin/activate      # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## 🔑 Step 2: Configuration & Credentials

To run the pipeline, you’ll need access to external services.

### **1. NVD API Key (Required)**

CVEye downloads vulnerability metadata directly from NVD.

1. Request an API key from NVD
2. Create a `.env` file in the project root
3. Add your key:

```
NVD_API_KEY=your_api_key_here
```

### **2. Google Cloud BigQuery (Required for Pipeline)**

The pipeline uses BigQuery for data processing.

1. Create a Service Account with BigQuery access
2. Download the JSON key
3. Save it as `credentials.json` in the project root (this file is ignored by Git)

---

## ⚙️ Step 3: Run the ML Pipeline

This process downloads raw data, merges datasets, generates features, and trains the model.

### **A. Add External Data**

Download the [CISA's KEV Catalog](https://www.cisa.gov/known-exploited-vulnerabilities-catalog) and place it into the `data/external/` folder.

### **B. Execute Processing & Training**

Run the ETL and modeling pipeline:

```bash
python3 project/pdpipeline/process.py
```

**Outputs:**

* Processed dataset → `data/merged/`
* Trained model → `models/logistic_regression_model.pkl`

---

## 🐳 Step 4: API Deployment (Docker + Cloud Run)

### **A. Local Testing with Docker**

Use the `--platform` flag to ensure compatibility (recommended for Apple Silicon).

```bash
# Build the API image (forces AMD64 for Cloud Run compatibility)
docker build --platform linux/amd64 -t cve_api_image .

# Run locally on port 8080
docker run -p 8080:8080 cve_api_image
```

Run tests:

```bash
pytest
```

### **B. Deploy to Google Cloud Run**

Ensure you have a `.gcloudignore` that excludes temporary files (e.g., `venv/`) but **includes** the `models/` folder.

Deploy:

```bash
gcloud run deploy cve-api-image \
  --source . \
  --port 8080 \
  --allow-unauthenticated
```

---

## 📂 Project Structure

```
├── Dockerfile
├── Makefile
├── README.md
├── requirements.txt
├── credentials.json        # GCP service account (ignored by Git)
├── .env                    # NVD API key (ignored by Git)
├── .gcloudignore
│
├── data
│   ├── external            # CISA KEV CSV
│   └── merged              # Final training data
│
├── models                  # Serialized ML models (.pkl)
│
└── project
    ├── app                 # FastAPI service
    │   ├── main.py
    │   └── schemas.py
    └── pdpipeline          # ETL, feature engineering, training
        └── process.py
```

---

## 📊 Key Model Metrics

| Metric    | Score |
| --------- | ----- |
| ROC-AUC   | 1.0   |
| Precision | 1.0   |
| Recall    | 1.0   |

---

## 🛠️ Tech Stack

**Core:** Python 3.10+, Pandas, NumPy
**ML:** Scikit-Learn, SHAP
**API:** FastAPI, Uvicorn
**Infra:** Docker, Google Cloud Run, BigQuery

---

If you'd like, I can also:
✅ Add badges (build, Python version, Cloud Run, license)
✅ Add examples of API requests/responses
✅ Add diagrams (ASCII or mermaid)
Just tell me!
