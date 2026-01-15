#!/bin/bash
# Example script for generating GitHub Copilot usage report
# 
# Usage:
#   1. Set your organization name and GitHub token as environment variables:
#      export GITHUB_ORG="your-organization-name"
#      export GITHUB_TOKEN="your-github-token"
#   
#   2. Run this script:
#      bash example_copilot_usage.sh
#
# Or pass parameters directly:
#   bash example_copilot_usage.sh your-org-name your-github-token

if [ $# -eq 2 ]; then
    # Arguments provided
    ORG_NAME=$1
    GITHUB_TOKEN=$2
    python copilot_usage_report.py --org "$ORG_NAME" --token "$GITHUB_TOKEN" --export-json
elif [ -n "$GITHUB_ORG" ] && [ -n "$GITHUB_TOKEN" ]; then
    # Environment variables set
    python copilot_usage_report.py --export-json
else
    echo "Error: Please provide organization name and GitHub token"
    echo ""
    echo "Usage option 1 - Set environment variables:"
    echo "  export GITHUB_ORG=\"your-organization-name\""
    echo "  export GITHUB_TOKEN=\"your-github-token\""
    echo "  bash example_copilot_usage.sh"
    echo ""
    echo "Usage option 2 - Pass as arguments:"
    echo "  bash example_copilot_usage.sh your-org-name your-github-token"
    echo ""
    echo "To create a GitHub token:"
    echo "  1. Go to GitHub Settings → Developer settings → Personal access tokens"
    echo "  2. Click 'Generate new token (classic)'"
    echo "  3. Select scopes: manage_billing:copilot and read:org"
    echo "  4. Generate and copy the token"
    exit 1
fi
