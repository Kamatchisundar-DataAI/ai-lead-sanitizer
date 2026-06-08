# ai-lead-sanitizer
A dynamic Streamlit application that leverages LLMs to clean corrupted lead data, normalize data formatting, and manage mixed data types seamlessly.


# 🧼 Universal AI-Powered Lead Sanitizer

A robust, enterprise-grade data cleaning application built with **Streamlit** and powered by **Gemini (via OpenRouter)**. This application solves a common B2B sales problem: cleaning up horribly corrupted lead lists, fixing international name encoding bugs, formatting phone numbers cleanly, and contextually splitting accidentally merged data strings.

## 🚀 Live Demo Check this Link..
👉 **https://ai-lead-sanitizer-5g8jzkmnyksfl23a5bkv9k.streamlit.app/**

---

## ✨ Features

* **🔀 Smart Positional Data Splitting:** Automatically detects rows with clumped, space-separated data (e.g., `bolo bol.com agale itok`) and distributes them cleanly into your existing structural columns (`Company` ➡️ `Website` ➡️ `First Name` ➡️ `Last Name`) without breaking rows that are already populated.
* **🔤 Strict English Text Cleansing:** Automatically strips away or translates unreadable text corruptions (like `?`) and removes foreign accent marks (transforming `Mariø` to `Mario` and `Ågale` to `Agale`).
* **💅 Global Case Standardization:** Forcefully formats all lead text strings, names, and job titles into professional, polished **Title Case**.
* **🛡️ Type-Crash Defenses (`int64` fix):** Built with custom Pandas data-type shields, preventing standard application failures when handling numerical columns like Phone Numbers or Zip Codes.
* **🧠 Intelligent Micro-Batching:** Processes heavy lead spreadsheets in smart chunks of 15 rows to maximize API efficiency and avoid token limit failures.

---

## 🛠️ Tech Stack

* **Frontend Dashboard:** Streamlit
* **Data Processing:** Python, Pandas
* **AI Core:** Google Gemini 2.5 Flash (via OpenRouter API connection)

---

## ⚙️ Local Setup and Installation

If you want to run this project locally on your machine, follow these quick steps:

### 1. Clone the repository
```bash
git clone [https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git)
cd YOUR_REPO_NAME

2. Install dependencies
Make sure you have Python installed, then run:
pip install streamlit pandas openai openpyxl

3. Configure Your Local Hidden Key
Create a folder named .streamlit and add a file inside it called secrets.toml:
# Inside .streamlit/secrets.toml
OPENROUTER_API_KEY = "your_secret_openrouter_api_key_here"

4. Boot Up the Dashboard
streamlit run app.py

How to Use the Application
Upload: Drop your messy .csv or .xlsx spreadsheet into the dropzone.

Map Splits (Optional): If a column has bunched-up text, select it from the dropdown to activate sequential column distribution.

Select Columns: Use the checkbox panel to choose exactly which columns you want the AI engine to fix.

Execute: Click Run Universal AI Correction Engine and watch the progress bar clean your file in real-time.

Download: Export your perfectly sanitized file back to a clean CSV!
