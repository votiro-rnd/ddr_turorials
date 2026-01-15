#!/usr/bin/env python3
"""
GitHub Copilot Usage Report Generator

This script fetches and displays GitHub Copilot usage statistics for an organization.
It requires a GitHub Personal Access Token with appropriate permissions.

Usage:
    python copilot_usage_report.py --org <organization_name> --token <github_token>

Or set environment variables:
    export GITHUB_ORG="your-org-name"
    export GITHUB_TOKEN="your-github-token"
    python copilot_usage_report.py
"""

import argparse
import os
import sys
from datetime import datetime
import requests
import json


class CopilotUsageReporter:
    """Client for fetching GitHub Copilot usage reports."""
    
    def __init__(self, org_name, token):
        """
        Initialize the Copilot Usage Reporter.
        
        Args:
            org_name (str): GitHub organization name
            token (str): GitHub Personal Access Token
        """
        self.org_name = org_name
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
    
    def get_copilot_seats(self):
        """
        Get Copilot seat assignments for the organization.
        
        Returns:
            dict: Copilot seat information
        """
        url = f"{self.base_url}/orgs/{self.org_name}/copilot/billing/seats"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"Error: Organization '{self.org_name}' not found or Copilot is not enabled.")
            elif e.response.status_code == 401:
                print("Error: Authentication failed. Please check your GitHub token.")
            elif e.response.status_code == 403:
                print("Error: Access forbidden. Make sure your token has 'manage_billing:copilot' scope.")
            else:
                print(f"Error: HTTP {e.response.status_code} - {e.response.text}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error: Failed to connect to GitHub API - {str(e)}")
            return None
    
    def get_copilot_usage(self):
        """
        Get Copilot usage metrics for the organization.
        
        Returns:
            list: Usage data for the organization
        """
        url = f"{self.base_url}/orgs/{self.org_name}/copilot/usage"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"Error: Usage data not available for organization '{self.org_name}'.")
            elif e.response.status_code == 401:
                print("Error: Authentication failed. Please check your GitHub token.")
            elif e.response.status_code == 403:
                print("Error: Access forbidden. Make sure your token has 'manage_billing:copilot' scope.")
            else:
                print(f"Error: HTTP {e.response.status_code} - {e.response.text}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error: Failed to connect to GitHub API - {str(e)}")
            return None
    
    def get_copilot_billing(self):
        """
        Get Copilot billing information for the organization.
        
        Returns:
            dict: Billing information
        """
        url = f"{self.base_url}/orgs/{self.org_name}/copilot/billing"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            # This endpoint might not be available or might have different permissions
            return None
        except requests.exceptions.RequestException:
            return None
    
    def format_seat_report(self, seats_data):
        """
        Format seat assignment data into a readable report.
        
        Args:
            seats_data (dict): Seat assignment data from GitHub API
        """
        if not seats_data:
            print("No seat data available.")
            return
        
        print("\n" + "=" * 80)
        print(f"GitHub Copilot Seat Report for Organization: {self.org_name}")
        print("=" * 80)
        
        total_seats = seats_data.get('total_seats', 0)
        seats = seats_data.get('seats', [])
        
        print(f"\nTotal Seats Allocated: {total_seats}")
        print(f"Active Seats: {len(seats)}")
        print("\n" + "-" * 80)
        
        if seats:
            print("\nSeat Assignments:")
            print(f"{'User':<30} {'Created At':<25} {'Last Activity':<25}")
            print("-" * 80)
            
            for seat in seats:
                assignee = seat.get('assignee', {})
                login = assignee.get('login', 'N/A')
                created_at = seat.get('created_at', 'N/A')
                last_activity = seat.get('last_activity_at', 'Never')
                
                # Format dates
                if created_at != 'N/A':
                    try:
                        created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        created_at = created_dt.strftime('%Y-%m-%d %H:%M:%S')
                    except (ValueError, AttributeError):
                        pass
                
                if last_activity and last_activity != 'Never':
                    try:
                        activity_dt = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
                        last_activity = activity_dt.strftime('%Y-%m-%d %H:%M:%S')
                    except (ValueError, AttributeError):
                        pass
                
                print(f"{login:<30} {created_at:<25} {last_activity:<25}")
        
        print("\n" + "=" * 80)
    
    def format_usage_report(self, usage_data):
        """
        Format usage metrics into a readable report.
        
        Args:
            usage_data (list): Usage metrics data from GitHub API
        """
        if not usage_data:
            print("\nNo usage data available.")
            return
        
        print("\n" + "=" * 80)
        print(f"GitHub Copilot Usage Metrics for Organization: {self.org_name}")
        print("=" * 80)
        
        if isinstance(usage_data, list) and len(usage_data) > 0:
            print("\nDaily Usage Statistics:")
            print(f"{'Date':<15} {'Suggestions':<15} {'Acceptances':<15} {'Lines Suggested':<20} {'Lines Accepted':<20}")
            print("-" * 80)
            
            total_suggestions = 0
            total_acceptances = 0
            total_lines_suggested = 0
            total_lines_accepted = 0
            
            for day_data in usage_data:
                date = day_data.get('day', 'N/A')
                suggestions = day_data.get('total_suggestions_count', 0)
                acceptances = day_data.get('total_acceptances_count', 0)
                lines_suggested = day_data.get('total_lines_suggested', 0)
                lines_accepted = day_data.get('total_lines_accepted', 0)
                
                total_suggestions += suggestions
                total_acceptances += acceptances
                total_lines_suggested += lines_suggested
                total_lines_accepted += lines_accepted
                
                print(f"{date:<15} {suggestions:<15} {acceptances:<15} {lines_suggested:<20} {lines_accepted:<20}")
            
            print("-" * 80)
            print(f"{'TOTAL':<15} {total_suggestions:<15} {total_acceptances:<15} {total_lines_suggested:<20} {total_lines_accepted:<20}")
            
            if total_suggestions > 0:
                acceptance_rate = (total_acceptances / total_suggestions) * 100
                print(f"\nOverall Acceptance Rate: {acceptance_rate:.2f}%")
        
        print("\n" + "=" * 80)
    
    def export_to_json(self, seats_data, usage_data, filename="copilot_usage_report.json"):
        """
        Export the usage report to a JSON file.
        
        Args:
            seats_data (dict): Seat assignment data
            usage_data (list): Usage metrics data
            filename (str): Output filename
        """
        report = {
            "organization": self.org_name,
            "generated_at": datetime.now().isoformat(),
            "seats": seats_data,
            "usage": usage_data
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\nReport exported to: {filename}")
        except Exception as e:
            print(f"Error exporting report: {str(e)}")
    
    def generate_report(self, export_json=False):
        """
        Generate a complete Copilot usage report.
        
        Args:
            export_json (bool): Whether to export the report to JSON
        """
        print(f"Fetching Copilot usage report for organization: {self.org_name}")
        print("Please wait...\n")
        
        # Fetch seat assignments
        seats_data = self.get_copilot_seats()
        if seats_data:
            self.format_seat_report(seats_data)
        else:
            print("\nFailed to fetch seat data. Please check your permissions and organization name.")
        
        # Fetch usage metrics
        usage_data = self.get_copilot_usage()
        if usage_data:
            self.format_usage_report(usage_data)
        else:
            print("\nFailed to fetch usage data. This might not be available for your organization.")
        
        # Export to JSON if requested
        if export_json and (seats_data or usage_data):
            self.export_to_json(seats_data, usage_data)


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Generate GitHub Copilot usage report for an organization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python copilot_usage_report.py --org my-org --token ghp_xxxxx
  python copilot_usage_report.py --org my-org --token ghp_xxxxx --export-json
  
Environment Variables:
  GITHUB_ORG      GitHub organization name
  GITHUB_TOKEN    GitHub Personal Access Token
  
Required Token Permissions:
  - manage_billing:copilot (for organization Copilot usage)
  - read:org (for organization information)
        """
    )
    
    parser.add_argument(
        '--org',
        type=str,
        help='GitHub organization name (or set GITHUB_ORG environment variable)'
    )
    
    parser.add_argument(
        '--token',
        type=str,
        help='GitHub Personal Access Token (or set GITHUB_TOKEN environment variable)'
    )
    
    parser.add_argument(
        '--export-json',
        action='store_true',
        help='Export report to JSON file'
    )
    
    args = parser.parse_args()
    
    # Get organization name
    org_name = args.org or os.environ.get('GITHUB_ORG')
    if not org_name:
        print("Error: Organization name is required.")
        print("Provide it via --org argument or GITHUB_ORG environment variable.")
        sys.exit(1)
    
    # Get GitHub token
    token = args.token or os.environ.get('GITHUB_TOKEN')
    if not token:
        print("Error: GitHub token is required.")
        print("Provide it via --token argument or GITHUB_TOKEN environment variable.")
        sys.exit(1)
    
    # Create reporter and generate report
    reporter = CopilotUsageReporter(org_name, token)
    reporter.generate_report(export_json=args.export_json)


if __name__ == "__main__":
    main()
