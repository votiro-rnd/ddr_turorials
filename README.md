# 🧠 Content Classification and PII Tutorials

This repository includes two hands-on tutorials:
- **Content Classification** – demonstrating text and PDF categorization using the `ContentClassificationClient`.
- **PII Detection & Masking** – demonstrating detection, masking, and threshold management using the `PiiClient`.

## 📊 GitHub Copilot Usage Report Tool

This repository also includes a tool to generate GitHub Copilot usage reports for organization owners.

### Quick Start for Copilot Usage Report

```bash
# Set your GitHub credentials
export GITHUB_ORG="your-organization-name"
export GITHUB_TOKEN="your-github-token"

# Run the usage report
python copilot_usage_report.py

# Or with command-line arguments
python copilot_usage_report.py --org your-org-name --token your-github-token

# Export to JSON file
python copilot_usage_report.py --export-json
```

**Required Token Permissions:**
- `manage_billing:copilot` - For accessing Copilot billing and usage data
- `read:org` - For reading organization information

**To create a token:**
1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Select the required scopes: `manage_billing:copilot` and `read:org`
4. Generate and copy the token

---

## 🚀 Getting Started (Quick Summary)

1. **Clone and setup the repository**
   ```bash
   git clone https://github.com/votiro-rnd/ddr_turorials.git  
   cd ddr_tutorials
   python -m venv venv   # recommended: py3.10 and higher
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Expose your virtual environment to Jupyter**
   ```bash
   python -m ipykernel install --user --name=venv --display-name "ddr-env"
   ```


## 🔐 Authentication

To connect to the DDR services, you’ll need an API auth key - contact us if you need one.

Set your key as an environment variable:
```bash
export AUTH_KEY="your-api-key"    # On Windows: set AUTH_KEY="your-api-key"
```

We will use this key in the notebooks.


3. **Launch the notebook**
> 💡 *Tip:* Make sure to launch jupyter from you venv ONLY after setting your AUTH_KEY as an ENV VAR (As described above)

   ```bash
   jupyter notebook
   ```
   Now in your browser (default http://localhost:8888) you can open any of the two tutorials  
      > **`/content_classification/notebooks/content_classification_basic_tutorial.ipynb`** or  
      > **`/pii/notebooks/pii_tutorial.ipynb`** and follow along.

---

## 🧱 Project Structure

```
content_classification_client_simple.py     # Lightweight Python client for the API
content_classification_basic_tutorial.ipynb  # Step-by-step Jupyter tutorial
requirements.txt                             # Dependency list
README.md                                   # Project overview and instructions
```

---

## 🧰 Running the Tutorial

Once the environment is prepared:
1. Open Jupyter Notebook or JupyterLab.
2. Select the kernel named **ddr-env**.
3. Follow the tutorial cells sequentially.

> 💡 *Tip:* you can also run `!pip install -r ../../requirements.txt` command from inside the notebook.  

---

## 📘 PII Tutorial Overview

The notebook covers:
1. **Detect sensitive data in both plain text and uploaded files**
2. **Mask detected entities while preserving the structure and readability of the source content**
3. **Visualize original and masked documents side by side for validation**
4. **Retrieve and update tenant-specific thresholds to control model sensitivity and confidence levels**

---

## 📘 Content Classification Tutorial Overview

The notebook covers:
1. **Client setup and configuration**
2. **Classifying a single file or text input**
3. **Working with categories and tags**
4. **Understanding global vs. tenant-specific categories**
5. **Viewing classification results and confidence scores**

---

## 🪪 License

© 2025 Votiro Cybersec LTD. All rights reserved.  
Distributed for demonstration and educational purposes only.

---

## 🙋 Support

For questions or feedback, please contact:  
📧 **support@votiro.com**
