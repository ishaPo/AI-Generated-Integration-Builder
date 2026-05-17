# AI-Integration-Builder

A Streamlit application that generates production-ready Python integration code from API prompts. This tool simplifies connecting external services and automates backend code generation using state-of-the-art LLMs.

## 🚀 Features

- **Automated Integration Code:** Generates clean, production-grade Python code based on natural language prompts.
- **Multi-LLM Powered:** Built to support integrations utilizing both Anthropic and Google Gemini APIs.
- **Streamlit Interface:** Clean, interactive UI for quick code generation and demo runs.

---

## 🛠️ Prerequisites

Before running this project, ensure you have Python 3.8+ installed on your system.

### 📦 Tech Stack
- **Framework:** Streamlit
- **Language:** Python
- **APIs supported:** Anthropic, Gemini, Calendly

---

## ⚙️ Installation & Setup

Follow these steps to set up the project locally:

### 1. Clone the Repository
```bash
git clone [https://github.com/YOUR_GITHUB_USERNAME/AI-Integration-Builder.git](https://github.com/YOUR_GITHUB_USERNAME/AI-Integration-Builder.git)
cd AI-Integration-Builder
```

### 2. Set Up a Virtual Environment
```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Required Dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables
Create a file named `.env` in the root directory of the project (**Note:** This file is included in `.gitignore` and should never be pushed to your public repository). 

Add the following environment variables to it:
```env
ANTHROPIC_API_KEY="your_anthropic_key_here"
GEMINI_API_KEY="your_gemini_key_here"
CALENDLY_TOKEN="your_calendly_token_here"
```

---

## 💻 How to Run the App

Launch the Streamlit web application by executing the following command in your terminal:

```bash
streamlit run app.py
```

The application should automatically open in your web browser at `http://localhost:8501`.

---

## 🔒 Security Note

Make sure your `.gitignore` file contains `.env` to prevent accidentally committing your API secrets to public repositories.
