# 🔄 Migration Planner: M365 to Google Workspace

A professional-grade estimation tool designed to plan and visualize data migration timelines. This tool bridges the gap between automated technical discovery and high-level project planning by offering both **Credential-based Scanning** and **Heuristic Manual Estimation**.

## 🚀 Live Application
**[INSERT STREAMLIT URL HERE]**

---

## ✨ Features

### 📂 Manual Data Entry (Heuristic Engine)
Designed for project managers and consultants to get instant estimates without needing Global Admin credentials.
* **Regional Intelligence**: Throughput is automatically calculated based on the selected Google Cloud target region.
* **Item-Volume Penalty**: Accounts for the "small file" overhead where high item counts slow down API performance.
* **Execution Batches**: Simulates parallel migration lanes to show how increasing concurrency impacts the "Go-Live" date.

### ⚙️ Automated Discovery
Interface shell designed to integrate with the Google `migration_planner.py` logic.
* Input fields for **Tenant ID**, **Client ID**, and **Client Secret**.
* Designed to crawl M365 environments locally via Microsoft Graph API.

---

## 📐 Estimation Logic & Math

The planner follows the official Google migration logic to ensure accuracy:

1. **Throughput Determination**:
   - **Base Mbps** is assigned based on the target data center region (e.g., US Multi-Region vs. Asia Southeast).
   - **Item Penalty** is applied: `Effective Speed = Base Speed / (1 + (Total Items / 100,000) * 0.05)`.

2. **Timeline Calculation**:
   - The total data is distributed across the number of **Parallel Lanes** (Execution Batches).
   - Time is calculated as: `(GB * 8192) / (Mbps * 3600)`.
   - A **25% API Latency Buffer** is added to account for M365 throttling, metadata handshakes, and network jitter.

---

## 🛠️ Installation & Local Usage

If you wish to run this planner locally on your machine:

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/migration-planner.git
cd migration-planner
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch the App
```bash
streamlit run app.py
```

---

## 📋 Project Structure
* `app.py`: The main Streamlit application containing the UI and logic.
* `requirements.txt`: List of Python dependencies (Streamlit, Pandas).
* `README.md`: Project documentation and logic explanation.

---

## ⚖️ Disclaimer
This tool provides estimates based on standard cloud performance benchmarks. Actual results may vary based on specific tenant throttling policies, network stability, and data complexity. This is an independent tool inspired by Google's migration planning scripts.
