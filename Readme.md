

# Ecochain AI 🌍

Ecochain AI is a sustainability intelligence app powered by **Google BigQuery**. It helps organizations analyze supplier data, measure eco-performance, and make data-driven sourcing decisions in real time.

---

## 🚀 Features

* **Dashboard:** Real-time sustainability analytics from BigQuery.
* **AI Assistant:** Natural language queries powered by BigQuery AI.
* **Supplier Onboarding:** Instant ingestion of new supplier data into BigQuery.

---

## 🛠️ Prerequisites

Before running Ecochain AI, make sure you have:

1. **Python 3.9+** installed.
2. A **Google Cloud project** with **BigQuery and Vertex AI enabled**.
3. A **Google Service Account** with billing enabled (required to query BigQuery).
4. Your **Service Account JSON key file** downloaded locally.

---

## ⚙️ Setup Instructions

1. **Clone the repository** (or download the project).

   ```bash
   git clone https://github.com/spotinforex/Ecochain-AI.git
   cd Ecochain-AI
   ```

2. **Create a virtual environment** (recommended to avoid package conflicts).

   ```bash
   python -m venv venv
   source venv/bin/activate   # On Mac/Linux
   venv\Scripts\activate      # On Windows
   ```

3. **Install dependencies** from `requirements.txt`.

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your service account**:

   * Open `src/config.py`.
   * Paste the **full path** to your JSON service account file in the `file_path` variable.
   * Paste your **Google Cloud project name** in the `project_path` variable.

   Example:

   ```python
   file_path = r"C:/Users/YourName/Downloads/service-account.json"
   project_path = "your-gcp-project-name"
   ```

5. **Run the app** (ensure you have internet connection):

   ```bash
   streamlit run app.py
   ```

6. The app will automatically open in your default web browser. 🎉

---

## 📌 Notes

* Make sure your service account is **linked to a billed Google Cloud project**; otherwise BigQuery queries won’t run.
* Keep your **JSON key file secure** and never commit it to GitHub.
* Use a virtual environment to prevent dependency issues.

---

## 🖼️ Demo

Ecochain demo showcases three main sections:

1. **Dashboard** – BigQuery-powered analytics.
2. **AI Assistant** – Ask questions in natural language.
3. **Supplier Onboarding** – Add and score new suppliers.

---

## 📄 License

This project is for educational and demo purposes.

