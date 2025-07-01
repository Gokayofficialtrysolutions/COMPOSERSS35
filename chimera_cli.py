#!/usr/bin/env python3
"""
Qoffee Explorer CLI - A command-line interface to interact with the Qoffee Explorer's API.
(Primarily for system health checks in the offline-focused version).
"""
import requests
import argparse
import json
import os
from urllib.parse import urljoin
import time # For potential future use with timestamps

# Default base URL for the Qoffee Explorer Jupyter server
DEFAULT_BASE_URL = "http://localhost:8887"

def get_base_url(args_base_url=None):
    """
    Gets base URL in order of precedence:
    1. Command-line argument (--base-url)
    2. Environment variable QOFFEE_BASE_URL
    3. DEFAULT_BASE_URL
    """
    if args_base_url and args_base_url != DEFAULT_BASE_URL:
        return args_base_url
    return os.getenv("QOFFEE_BASE_URL", DEFAULT_BASE_URL)

def handle_response(response, args, custom_formatter=None):
    """
    Prints formatted response.
    If args.json is True, prints raw JSON.
    Otherwise, if custom_formatter is provided, uses it.
    Otherwise, prints basic status and text/JSON.
    """
    print(f"Status Code: {response.status_code}")
    if args.json:
        try:
            print("Response JSON:")
            print(json.dumps(response.json(), indent=2))
        except json.JSONDecodeError:
            print("Response Text (not valid JSON):")
            print(response.text)
    elif custom_formatter:
        custom_formatter(response)
    else:
        try:
            print("Response JSON:")
            print(json.dumps(response.json(), indent=2))
        except json.JSONDecodeError:
            print("Response Text:")
            print(response.text)

def _format_health_status(response):
    """Custom formatter for health status output."""
    try:
        data = response.json()
        print("\n--- Qoffee Explorer System Health ---")
        print(f"  Overall Status: {data.get('overall_status', 'UNKNOWN')}")
        print(f"  Timestamp: {data.get('timestamp', 'N/A')}")

        print("\n  Services:")
        for service_name, service_info in data.get("services", {}).items():
            display_name = service_name.replace('_', ' ').title()
            print(f"    {display_name}:")
            print(f"      Status: {service_info.get('status', 'UNKNOWN')}")
            print(f"      Message: {service_info.get('message', 'N/A')}")
            if service_info.get('details'):
                 print(f"      Details: {json.dumps(service_info.get('details'))}")

        # Queues section might be minimal or removed if not relevant to offline explorer's health endpoint
        if "queues" in data and data["queues"] is not None: # Check if queues key exists and is not None
            queues_data = data.get("queues", {})
            # Only print if relevant queue data exists (it might be empty for offline explorer)
            if "active_commands" in queues_data or "failed_commands" in queues_data :
                print("\n  Backend Queues (if applicable):")
                print(f"    Active Commands: {queues_data.get('active_commands', 'N/A')}")
                print(f"    Failed Commands: {queues_data.get('failed_commands', 'N/A')}")
        print("---")

    except json.JSONDecodeError:
        print("Error: Could not parse JSON response for health status.")
        print(f"Raw Response Text:\n{response.text}")
    except Exception as e:
        print(f"Error formatting health status: {e}")
        print(f"Raw Response Text:\n{response.text}")

def get_health_status(args):
    """Fetches and displays the system health status."""
    base_url = get_base_url(args.base_url)
    url = urljoin(base_url, "/api/health")
    print(f"Fetching system health from {url}...")
    try:
        response = requests.get(url, timeout=10)
        if response.ok:
            handle_response(response, args, custom_formatter=_format_health_status)
        else:
            handle_response(response, args) # Show default error format for non-ok responses
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Qoffee Explorer API: {e}")

def main():
    parser = argparse.ArgumentParser(description="Qoffee Explorer Command Line Interface")
    parser.add_argument('--base-url', default=os.getenv("QOFFEE_BASE_URL", DEFAULT_BASE_URL),
                        help=f"Base URL of the Qoffee Explorer Jupyter server (default: {DEFAULT_BASE_URL} or QOFFEE_BASE_URL env var)")
    parser.add_argument('--json', action='store_true', help="Output raw JSON response instead of formatted text.")

    subparsers = parser.add_subparsers(title="commands", dest="command", required=True)

    # Health check command
    health_parser = subparsers.add_parser("health", help="Get system health check status.")
    health_parser.set_defaults(func=get_health_status)

    # Removed Home Connect specific commands: status, retry, delete, list-machines, reset-offline-data

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
