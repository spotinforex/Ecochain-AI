# Ecochain AI 🌍

Ecochain AI is a sustainability intelligence app powered by **Google BigQuery**.  
It helps organizations analyze supplier data, measure eco-performance, and make data-driven sourcing decisions in real time.

---

## ⚡ Quick Start

If you already have Python, Google Cloud SDK, and a service account key set up, run these commands:

```bash
# 1. Clone the repo
git clone https://github.com/spotinforex/Ecochain-AI.git
cd Ecochain-AI

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create BigQuery test connection (Don't change connection name)
bq mk --connection --connection_type=CLOUD_RESOURCE --location=US test_connection

# 5. Grant Vertex AI permissions (replace YOUR_PROJECT_ID and `SERVICE_ACCOUNT_EMAIL`)
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:`SERVICE_ACCOUNT_EMAIL`" \
  --role="roles/aiplatform.user" \
  --role="roles/bigquery.connectionUser"

# 6. Run the app
streamlit run app.py
````

> ⚠️ Replace `YOUR_PROJECT_ID` with your actual Google Cloud project ID and `SERVICE_ACCOUNT_EMAIL` with your service account email. Make sure your `src/config.py` contains the correct path to your service account JSON file and Project ID.

---

## 🚀 Features

* **Dashboard:** Real-time sustainability analytics from BigQuery.
* **AI Assistant:** Natural language queries powered by BigQuery AI.
* **Supplier Onboarding:** Instant ingestion of new supplier data into BigQuery.

---

## 🛠️ Prerequisites

Before running Ecochain AI, make sure you have:

1. **Python 3.9+** installed.
2. A **Google Cloud project** with **BigQuery,BigQuery Connection and Vertex AI APIs enabled**.
3. A **Google Service Account** with billing enabled (required to query BigQuery).
4. Your **Service Account JSON key file** downloaded locally.
5. **Google Cloud SDK (gcloud + bq CLI)** installed and authenticated with your project.

---

## ⚙️ Setup Instructions

*(Detailed steps for users who need more guidance — see Quick Start above if you’re already familiar)*

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
   * Paste your **Google Cloud project ID** in the `project_id` variable.

   Example:

   ```python
   file_path = r"C:/Users/YourName/Downloads/service-account.json"
   project_id = "your-gcp-project-id"
   ```

5. **Create a BigQuery connection** for Ecochain AI Assistant (run in your Cloud SDK terminal):

   ```bash
   bq mk --connection --connection_type=CLOUD_RESOURCE --location=US test_connection
   ```

   > ⚠️ Do not change `test_connection` (This connection name is necessary for the app).

6. **Grant Vertex AI permissions** to BigQuery (replace `YOUR_PROJECT_ID` with your actual project ID and `SERVICE_ACCOUNT_EMAIL` with your provided service account email):

   ```bash
   gcloud projects add-iam-policy-binding `YOUR_PROJECT_ID`  --member="serviceAccount:`SERVICE_ACCOUNT_EMAIL`" --role="roles/aiplatform.user" --role="roles/bigquery.connectionUser"
   ```

7. **Run the app**:

   ```bash
   streamlit run app.py
   ```

8. The app will automatically open in your default web browser. 🎉

---

## 📌 Notes

* Your service account must be linked to a **billed Google Cloud project**; otherwise BigQuery queries won’t run.
* Keep your **JSON key file secure** and never commit it to GitHub.
* Use a virtual environment to prevent dependency issues.
* Ensure the project on your Google SDK matches that of your Service Account Key file
* Similarity Questions that require the use of VECTOR_SEARCH may not work as they require special access. Do well to contact developer for access
* Adding New Suppliers will also require special access to edit database, Do well to contact developer

---

## 🖼️ Demo

Ecochain demo showcases three main sections:

1. **Dashboard** – BigQuery-powered analytics.
2. **AI Assistant** – Ask questions in natural language.
3. **Supplier Onboarding** – Add and score new suppliers.

Demo Video Link: [https://youtu.be/ZXmJ6XZkVJQ?feature=shared](https://youtu.be/ZXmJ6XZkVJQ?feature=shared)

---

## Fixes

Errors that maybe encountered:
1. **Permission Error**
```bash
   ERROR:root:AI.GENERATE Failed to Generate Output: 400 bqcx-152278246826-5i3e@gcp-sa-bigquery-condel.iam.gserviceaccount.com does not have the permission to access resources used by AI.GENERATE.
   ```
**Fix**: Use the displayed Service Account,for example:bqcx-152278246826-5i3e@gcp-sa-bigquery-condel.iam.gserviceaccount.com when granting Vertex AI Permission

## 📄 License

This project is Under the Apache License.


