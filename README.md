# Automated Signup Flow

**Task:** Automate the signup process of the following site:
(https://authorized-partner.netlify.app/login)

This script automate the entire signup flow end-to-end with (no manual intervention required) 
It uses a temporary email from [Mail.tm](https://mail.tm) to receive OTPs automatically, ensuring a clean test environment for each run.

## Environment & Setup

**Language:** Python 3.12.0
**Framework:** [Playwright for Python](https://playwright.dev/python/) (async API) 

## Installation
1. Clone this repository
```bash
git clone https://github.com/subod4/Vrit_Q.git
```

2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate   # Linux / macOS
venv\Scripts\activate      # Windows
```
3. Install dependencies
```bash
pip install -r requirements.txt
playwright install
```
4. Run the Script
```bash 
python signup_automation_script.py
```
