# CVEye

### *A Machine Learning Lens on Exploitable Vulnerabilities*

CVEye is a predictive analytics platform that estimates the real-world exploitation risk of known security vulnerabilities (CVEs). By combining data from **NVD** and **CISA KEV**, CVEye produces a probability score indicating whether a vulnerability is likely to be exploited in the wild—empowering security teams to prioritize remediation with confidence.

---

# 📌 1. Project Overview & Goals

Modern vulnerability databases track thousands of CVEs each year, but only a fraction are actively exploited. CVEye aims to:

* Predict whether a CVE is likely to be exploited.
* Provide a machine-learning–driven risk score for prioritization.
* Automate ingestion and processing of vulnerability metadata.
* Offer a deployable API for real-time predictions.
* Deliver a lightweight front-end for interacting with model results.

---

# 📦 2. Dataset Description

CVEye integrates two major datasets:

### **1. National Vulnerability Database (NVD)**
* NVD [API Key Link (developers)](https://nvd.nist.gov/developers/request-an-api-key)
* Source of core CVE metadata: CVSS, CWE, descriptions, severity, etc.
* Pulled using the optional NVD API key.
* Format: JSON.

### **2. CISA Known Exploited Vulnerabilities (KEV) Catalog**
* KEV [Website Link](https://www.cisa.gov/known-exploited-vulnerabilities-catalog)
* Provides ground-truth exploitation labels.
* Manually downloaded as CSV into `data/external/`.

### **Merged Dataset**

All datasets are processed and joined in BigQuery and output to:

```
data/merged/Main1.csv
```

---

# 🤖 3. Model Architecture & Evaluation

### **Model Architecture**

The ML pipeline includes:

* Feature extraction from NVD (CVSS metrics, CWE, textual data)
* Feature engineering using Pandas & BigQuery SQL
* Logistic Regression model (baseline)
* Model serialization via pickle → `models/logistic_regression_model.pkl`

### **Evaluation Metrics**

| Metric    | Score |
| --------- | ----- |
| Accuracy  | 1.0   |
| ROC-AUC   | 1.0   |
| Precision | 1.0   |
| Recall    | 1.0   |

Here’s a clean, GitHub-ready way to integrate **W&B metric visualization** directly into your *Model Architecture & Evaluation* section.
I’ll add it **without disrupting your structure**, and in a style consistent with the rest of the README.

---

### **Model Architecture**

The ML pipeline includes:

* Feature extraction from NVD (CVSS metrics, CWE, textual data)
* Feature engineering using Pandas & BigQuery SQL
* Logistic Regression model (baseline)
* Model serialization via pickle → `models/logistic_regression_model.pkl`

---

### **Evaluation Metrics**

| Metric    | Score |
| --------- | ----- |
| Accuracy  | 1.0   |
| ROC-AUC   | 1.0   |
| Precision | 1.0   |
| Recall    | 1.0   |

*(These values reflect the most recent training output—subject to change based on dataset updates.)*

---

### 📈 **Viewing Model Metrics in Weights & Biases (W&B)**

CVEye tracks all training runs, metrics, and artifacts using **Weights & Biases**.

To view training dashboards:

1. Log in to W&B

   ```bash
   wandb login
   ```

2. Open the project dashboard:
   **[https://wandb.ai/](https://wandb.ai/alexoh2020-duke-university/CVE-logreg-pipeline)**

3. Once a project member shares dashboard access, you can explore:

   * Training & validation curves
   * ROC-AUC over time
   * Precision/recall trends
   * Confusion matrices
   * Model artifacts (logged `.pkl` files)
   * System metrics (CPU, GPU, memory usage)



---

# ☁️ 4. Cloud Services Used

| Service                      | Purpose                                                   |
| ---------------------------- | --------------------------------------------------------- |
| **Google BigQuery**          | Centralized storage, feature engineering, data processing |
| **Google Cloud Run**         | Deployment of FastAPI prediction service                  |
| **Google Artifact Registry** | (Optional) Stores versioned Docker images                 |
| **Google IAM**               | Handles service account privileges                        |

---

# 🛠️ 5. Setup & Usage Instructions

## 🔧 Environment Setup

```bash
git clone https://github.com/your-username/Project_CVE.git
cd Project_CVE

python -m venv venv
source ./venv/bin/activate   # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

---

## 🔑 Configuration & Credentials

### **NVD API Key (optional)**

Create `.env`:
Get an NVD API key [here](https://nvd.nist.gov/developers/)

```
NVD_API_KEY=your_api_key_here
```

### **Google Cloud BigQuery (required)**

Save GCP service account key as:

```
credentials.json
```

---

## ⚙️ Running the ML Pipeline

### 1. Add External Data

Download CISA KEV CSV → place into:

```
data/external/
```

### 2. Run End-to-End Pipeline

```bash
source ./run_ingestion.sh
```

Or run the second half of the pipeline with components pulling data from BigQuery and training LRmodel:

```bash
# Pull data from BigQuery, Train / Test Split, and produce processor
python3 project/pdpipeline/mlpipeline.py
# Train LR model
python3 project/modeling/LRmodel.py
```

**Outputs:**

* Processed data → `data/merged/`
* Model → `models/logistic_regression_model.pkl`

---

# 🐳 6. Deploying the API (Docker + Cloud Run)

### A. Local Testing

```bash
docker build --platform linux/amd64 -t cve_api_image .
docker run -p 8080:8080 cve_api_image
```

### B. Deploy to Google Cloud Run

```bash
gcloud run deploy cve-api-image \
  --source . \
  --port 8080 \
  --allow-unauthenticated
```

---

# 🔗 7. Links to Deployed Services

> Replace these with your actual deployment URLs

| Service                  | URL                                                            |
| ------------------------ | -------------------------------------------------------------- |
| **CVE Prediction API** | [https://cve-api-image-499266163270.us-east1.run.app](https://cve-api-image-499266163270.us-east1.run.app) |
| **CVEye Front-End App**  | [https://projectcve-874mkb2crban6nve6devfv.streamlit.app/](https://projectcve-874mkb2crban6nve6devfv.streamlit.app/)         |

---

# 📂 8. Project Structure
Run tests of the deployed api:

```bash
pytest
```

# 🌐 9: Streamlit App Front-end

You can drive the public API with a lightweight Streamlit UI.

**Run locally**

```bash
pip install -r frontend/requirements.txt
API_URL=http://localhost:8000/predict 
streamlit run frontend/app.py
```


**Live app URL:**
[https://projectcve-874mkb2crban6nve6devfv.streamlit.app/](https://projectcve-874mkb2crban6nve6devfv.streamlit.app/).

**What the front-end does**

- Collects CVSS-style inputs (scores and categories), uses the saved preprocessor (`data/traintest/preprocessor.joblib`) to expand them into the 91-feature vector expected by the model, and sends them to `/predict`.
- Shows predicted class (Not Exploited / Likely Exploited) with confidence; highlights “High” only when class=1 and above the adjustable threshold.
- Defaults to the Cloud Run API URL you provided; override via env vars if needed.

## 📂 Project Structure

```
├── Dockerfile
├── Makefile
├── README.md
├── requirements.txt
├── credentials.json        # GCP service account (ignored)
├── .env                    # NVD API key (ignored)
│
├── frontend                # frontend streamlit app 
├── data
│   ├── external            # CISA KEV CSV
│   └── merged              # Final training data
│
├── models                  # Trained ML models (.pkl)
│
├── data/traintest
│   ├── preprocessor.joblib        # Saved ColumnTransformer (used by Streamlit UI)
│   └── feature_metadata.joblib    # Feature names/metadata (used by Streamlit UI)
│
└── project
    ├── app                 # FastAPI service
    │   ├── main.py
    │   └── schemas.py
    └── pdpipeline          # ETL + Modeling pipeline
        └── process.py
```

---

# 🛠️ Tech Stack

* **Python**, Pandas, NumPy
* **Scikit-Learn**, SHAP
* **FastAPI**, Uvicorn
* **Docker**, **Cloud Run**, **BigQuery**

---

Assistance: parts of this project (including the Streamlit front-end wiring and documentation) were completed with Codex on 2025-11-24.
# 📚 Referenced AI

FastAPI Code: [https://gemini.google.com/share/0660dc2e3cbd](https://gemini.google.com/share/0660dc2e3cbd)
Deploy ML Code: [https://gemini.google.com/share/95cc22ffd1ec](https://gemini.google.com/share/95cc22ffd1ec)
VL Interpretability: [https://gemini.google.com/share/c656d0762764](https://gemini.google.com/share/c656d0762764)
README: [https://gemini.google.com/app/e4e03351e78bbfa8
](https://gemini.google.com/app/e4e03351e78bbfa8)


