<h1 align="center">🧠 SmartDoc — AI-Powered Document Analysis Platform</h1>

<p align="center">
  <a href="https://www.youtube.com/shorts/uhTLxG_UQ34"><img src="https://img.shields.io/badge/🎥%20Watch%20Demo-YouTube-red"></a>
  <img src="https://img.shields.io/badge/Deployed%20on-Google%20Cloud%20Run-blue">
</p>

---

## 🚀 Overview

**SmartDoc** is an AI-powered document intelligence system that extracts and structures key fields from invoices, receipts, and business documents.

It integrates:

- 🧠 **Kimi K2 (Moonshot AI)** — cost-efficient LLM for structured field extraction  
- 🔤 **Tesseract OCR** — text recognition from scanned docs  
- ⚙️ **FastAPI** backend instrumented with Prometheus metrics  
- 🪶 **Streamlit** frontend for interactive visualization  
- 💾 **PostgreSQL** database for persistent storage  
- 📊 **Prometheus + Grafana** for observability  
- 🔁 **GitHub Actions → Cloud Run** for automated CI/CD deployment  

---

```markdown
## 🧩 System Architecture

```text
[ Streamlit Frontend ]
│
▼
[ FastAPI Backend ]
├── OCR (Tesseract)
├── LLM Parsing (Kimi K2)
├── Prometheus /metrics
└── PostgreSQL Database
│
▼
[ Prometheus Scraper ] → [ Grafana Dashboards ]
│
▼
[ GitHub Actions → Cloud Run (CI/CD) ]
```

Flow Summary:
Frontend sends documents → Backend extracts text and parses fields → Metrics exposed via Prometheus → Visualized in Grafana → Deployed automatically via GitHub Actions to Cloud Run.

🎥 Demo Video
▶️ https://www.youtube.com/shorts/uhTLxG_UQ34

---


## 📸 Screenshots

### 🧾 Frontend
Streamlit document upload & extracted JSON output  
<img src="assets/frontend.png" width="600" align="left">

<br clear="left"/>

### ⚙️ Metrics Endpoint
`/metrics` response with custom Prometheus counters & histograms  
<img src="assets/metrics-endpoint.png" width="600" align="left">

<br clear="left"/>

### 📊 Grafana Dashboard
Real-time monitoring: document throughput, latency, CPU time  
<img src="assets/grafana.png" width="600" align="left">

<br clear="left"/>

### 🚀 GitHub Actions
Automated multi-service build and deploy pipeline  
<img src="assets/github-actions.png" width="600" align="left">

<br clear="left"/>



## 🧾 Prometheus Metrics

Custom metrics exposed by the backend:

| Metric | Description |
|---------|-------------|
| `smartdoc_documents_processed_total{status}` | Total documents processed (success / failed) |
| `smartdoc_ocr_confidence` | OCR confidence distribution |
| `smartdoc_llm_call_duration_seconds` | Time spent calling the LLM API |
| `smartdoc_document_processing_duration_seconds` | End-to-end processing duration |
| `smartdoc_active_processing` | Number of active document jobs |

All metrics are available at the backend’s `/metrics` endpoint  
and can be scraped by Prometheus, then visualized in Grafana.

---

## ☁️ CI/CD Automation (GitHub Actions)

SmartDoc uses a single GitHub Actions workflow to:

1. **Authenticate** to Google Cloud with a service account  
2. **Build & push** Docker images for:
   - Backend  
   - Frontend  
   - Prometheus  
   - Grafana  
3. **Deploy** each service to Cloud Run  
4. **Inject secrets** from GCP Secret Manager  
   (`OPENAI_API_KEY`, `KIMI_API_KEY`, `POSTGRES_URL`, etc.)  
5. **Print deployment URLs** for quick access  

This makes the entire stack reproducible even if you shut everything down and redeploy later.

---
## 🧰 Local Setup

### 1️⃣ Clone the Repository

```bash
# Clone the SmartDoc repository
git clone https://github.com/anand-amon/smart-doc.git

# Navigate into the project folder
cd smart-doc
```

### 2️⃣ Create `.env`

In the project root, create a new file named `.env` and add the following:

```bash
# 🔑 API Keys
OPENAI_API_KEY=your_openai_key
KIMI_API_KEY=your_kimi_key

# 🗄️ Database Connection
POSTGRES_URL=postgresql://user:password@localhost:5432/smartdoc

# ⚙️ App Configuration
ENABLE_METRICS=true
USE_KIMI_API=true

# 📂 Directory Paths
UPLOAD_DIR=./uploads
PROCESSED_DIR=./processed
```



### 3️⃣ Run Locally

```bash
docker compose up --build
```

Then visit:

Frontend → http://localhost:8501

Backend → http://localhost:8000

Prometheus → http://localhost:9090

Grafana → http://localhost:3000


## 🧠 Tech Stack

| Category | Technology |
|-----------|-------------|
| 🖥️ Frontend | Streamlit |
| ⚙️ Backend | FastAPI, Pydantic |
| 🤖 AI | Tesseract OCR, Kimi K2 (Moonshot AI) |
| 🗄️ Database | PostgreSQL |
| 📊 Monitoring | Prometheus, Grafana |
| 🚀 CI/CD | Docker, GitHub Actions, Cloud Run |

## 🧪 Example API Call

You can test the SmartDoc backend by uploading a document (e.g., an invoice) via `curl`:

```bash
curl -X POST \
  -F 'file=@invoice.png' \
  http://localhost:8000/upload
```


```json
{
  "invoice_number": "554951",
  "date": "14 MAY, 2015",
  "total_amount": "86.43",
  "vendor": "Smith Inc"
}
```


## 📈 Example PromQL Queries

You can use these queries directly in **Prometheus** or **Grafana** to monitor your SmartDoc system performance.

```bash
# Rate of successfully processed documents (per 5-minute window)
rate(smartdoc_documents_processed_total{status="success"}[5m])

# 90th percentile LLM API latency
histogram_quantile(
  0.9,
  sum(rate(smartdoc_llm_call_duration_seconds_bucket[5m])) by (le)
)
```

---

## 🏁 License

© 2025 Anand Amon. All rights reserved.  
This project is intended for educational and demonstration purposes.

---

## 🙌 Acknowledgments

Grateful thanks to the open-source and cloud tools that made **SmartDoc** possible:

- 🧠 **Moonshot AI — Kimi K2** for cost-efficient large language model inference  
- 🔤 **Tesseract OCR (Document Text Recognition)** for OCR-based text extraction  
- ☁️ **Google Cloud** for Cloud Run, Cloud SQL, and Secret Manager  
- 📊 **Prometheus & Grafana** for monitoring and observability  
- ⚙️ **Streamlit & FastAPI** for rapid app development
