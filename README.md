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

