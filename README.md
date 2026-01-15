# 🧠 Content Classification and PII Tutorials

This repository includes two hands-on tutorials:
- **Content Classification** – demonstrating text and PDF categorization using the `ContentClassificationClient`.
- **PII Detection & Masking** – demonstrating detection, masking, and threshold management using the `PiiClient`.

## 📊 GitHub Copilot Usage Report Tool

This repository also includes a tool to generate GitHub Copilot usage reports for organization owners. If you're experiencing issues with the GitHub UI button not responding when trying to view usage reports, this command-line tool provides a reliable alternative.

### What This Tool Does

The Copilot Usage Report tool fetches and displays:
- **Seat Assignments**: List of all users with Copilot access, when they were added, and their last activity
- **Usage Metrics**: Daily statistics including suggestions, acceptances, and acceptance rates
- **Export Options**: Save reports as JSON for further analysis

### Quick Start for Copilot Usage Report

**Option 1: Using environment variables**
```bash
# Set your GitHub credentials
export GITHUB_ORG="your-organization-name"
export GITHUB_TOKEN="your-github-token"

# Run the usage report
python3 copilot_usage_report.py

# Export to JSON file
python3 copilot_usage_report.py --export-json
```

**Option 2: Using command-line arguments**
```bash
python3 copilot_usage_report.py --org your-org-name --token your-github-token
```

**Option 3: Using the example script**
```bash
# Make it easy with the included example script
bash example_copilot_usage.sh your-org-name your-github-token
```

### Creating a GitHub Token

To use this tool, you need a GitHub Personal Access Token with the right permissions:

1. Go to [GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Give it a descriptive name (e.g., "Copilot Usage Reporter")
4. Select the following scopes:
   - ✅ `manage_billing:copilot` - For accessing Copilot billing and usage data
   - ✅ `read:org` - For reading organization information
5. Click "Generate token"
6. Copy the token immediately (you won't be able to see it again!)

### Example Output

```
================================================================================
GitHub Copilot Seat Report for Organization: your-org
================================================================================

Total Seats Allocated: 10
Active Seats: 8

--------------------------------------------------------------------------------
Seat Assignments:
User                           Created At                Last Activity            
--------------------------------------------------------------------------------
john.doe                       2024-01-15 10:30:00      2024-01-14 16:45:00     
jane.smith                     2024-01-10 09:15:00      2024-01-14 18:22:00     
...
================================================================================
```

### Troubleshooting

- **401 Authentication Error**: Check that your token is valid and hasn't expired
- **403 Forbidden Error**: Verify your token has the `manage_billing:copilot` and `read:org` scopes
- **404 Not Found Error**: Confirm the organization name is correct and Copilot is enabled
- **No Usage Data**: Usage metrics may take time to populate after Copilot activation

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
copilot_usage_report.py                      # GitHub Copilot usage report generator
example_copilot_usage.sh                     # Example script for running the usage report
content_classification/                      # Content classification tutorial
  src/content_classification_client_simple.py  # Lightweight Python client for the API
  notebooks/content_classification_basic_tutorial.ipynb  # Step-by-step Jupyter tutorial
pii/                                         # PII detection and masking tutorial
  src/pii_client.py                           # PII client implementation
  notebooks/pii_tutorial.ipynb                # PII tutorial notebook
query_files/                                 # Sample files for testing
requirements.txt                             # Dependency list
README.md                                    # Project overview and instructions
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
