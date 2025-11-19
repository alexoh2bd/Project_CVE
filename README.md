# Project_CVE
Cyber Security Risk Assessment Platform

# CVE 🔍🛡️  
_A Machine Learning Lens on Exploitable Vulnerabilities_

CVEye is a predictive analytics project that assesses the real-world exploitation risk of known vulnerabilities (CVEs) using publicly available datasets and machine learning models. The goal is to help security researchers and engineers prioritize patching and mitigation by forecasting which vulnerabilities are most likely to be exploited in the wild.

---

## 🚀 Project Goals

- Predict whether a CVE is likely to be exploited using historical and real-time metadata.
- Combine data from the NVD, CISA KEV, EPSS, and ExploitDB to train models.
- Build interpretable models for decision-making in security operations.
- Enable a lightweight pipeline for ingesting new CVEs and generating risk scores.

---

## 🔍 Key Features

- **Multi-source enrichment**: Combines CVSS scores, exploit availability, exposure age, and EPSS data.
- **Real-world label**: Uses [CISA's KEV Catalog](https://www.cisa.gov/known-exploited-vulnerabilities-catalog) as ground truth for exploitation.
- **Binary classification**: Predicts whether a CVE will be exploited (`1`) or not (`0`).
- **Model comparison**: Benchmarks logistic regression vs. random forest classifiers.
- **Feature importance analysis**: Highlights key predictors of exploitation.

---

## 📊 Key Metrics

- **ROC-AUC**
- **Precision / Recall**
- **Top-k prioritization effectiveness**
- **Feature importances**

---

## 🛠️ Tech Stack

- **Language**: Python 3.10+
- **Data Tools**: `pandas`, `numpy`, `requests`, `BeautifulSoup4`
- **ML Tools**: `scikit-learn`, `matplotlib`, `seaborn`, `shap`
- **Sources**:
  - [NVD (National Vulnerability Database)](https://nvd.nist.gov/vuln/data-feeds)
  - [CISA KEV Catalog](https://www.cisa.gov/known-exploited-vulnerabilities-catalog)
  - [EPSS (Exploit Prediction Scoring System)](https://www.first.org/epss/)
  - [ExploitDB](https://www.exploit-db.com/)
  - [Common Weakness Enumeration](https://cwe.mitre.org/data/)

---

## 🧠 Example Features

| Feature Name        | Description                                  |
|---------------------|----------------------------------------------|
| `cvss_score`        | Base CVSS 3.x score                          |
| `epss_score`        | Probability of exploit in the next 30 days   |
| `exploitdb_hits`    | Number of public exploits found              |
| `days_since_publish`| Time since CVE was first disclosed           |
| `vector_AV`         | Attack Vector (Local/Network/Adjacent)       |
| `vector_AC`         | Attack Complexity (Low/High)                 |
| `cwe_category`      | Type of vulnerability                        |

---

## 📂 Project Structure


```
├── LICENSE            <- Open-source license if one is chosen
├── Makefile           <- Makefile with convenience commands like `make data` or `make train`
├── README.md          <- The top-level README for developers using this project.
├── data
│   ├── external       <- Data from third party sources.
│   ├── interim        <- Intermediate data that has been transformed.
│   ├── processed      <- The final, canonical data sets for modeling.
│   └── raw            <- The original, immutable data dump.
│
├── docs               <- A default mkdocs project; see www.mkdocs.org for details
│
├── models             <- Trained and serialized models, model predictions, or model summaries
│
├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
│                         the creator's initials, and a short `-` delimited description, e.g.
│                         `1.0-jqp-initial-data-exploration`.
│
├── pyproject.toml     <- Project configuration file with package metadata for 
│                         project_cve and configuration for tools like black
│
├── references         <- Data dictionaries, manuals, and all other explanatory materials.
│
├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
│   └── figures        <- Generated graphics and figures to be used in reporting
│
├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
│                         generated with `pip freeze > requirements.txt`
│
├── setup.cfg          <- Configuration file for flake8
│
└── project_cve   <- Source code for use in this project.
    │
    ├── __init__.py             <- Makes project_cve a Python module
    │
    ├── config.py               <- Store useful variables and configuration
    │
    ├── dataset.py              <- Scripts to download or generate data
    │
    ├── features.py             <- Code to create features for modeling
    │
    ├── modeling                
    │   ├── __init__.py 
    │   ├── predict.py          <- Code to run model inference with trained models          
    │   └── train.py            <- Code to train models
    │
    └── plots.py                <- Code to create visualizations
```

--------


## Setup Environment and Prereq files

After cloning the environment 
`
python -m venv venv
source ./venv/bin/activate
pip install -r requirements.txt
`
### GCP Setup
To access Google Cloud BigQuery, we save a service account key in our repository as 'credentials.json'. 


### Data sources
We need NVD and Known Exploited Vulnerabilities (KEV) 

They can be found at these websites

#### NVD
  National Vulnerabilities Database
  This is the main National Vulnerabilities data source
  https://nvd.nist.gov/<br>
  Get an API key [here](https://nvd.nist.gov/developers/request-an-api-key) and store it in a .env file in the root directory as NVD_API_KEY.

#### KEV  
  https://www.cisa.gov/known-exploited-vulnerabilities-catalog
  Found under 'CSV'.

You can run the pipeline through the following script:
```
python3 project/pdpipeline/process.py
```

The final data should populate /data/merged directory
