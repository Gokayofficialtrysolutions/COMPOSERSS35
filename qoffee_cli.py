#!/usr/bin/env python3
"""
Qoffee-Maker CLI - A command-line interface to interact with the QoffeeMaker's API.
"""
import requests
import argparse
import json
import os
from urllib.parse import urljoin

# Default base URL for the QoffeeMaker Jupyter server
DEFAULT_BASE_URL = "http://localhost:8887"
# Path to a file that might store the XSRF token (e.g., after a manual login via browser)
# This is a simplistic way to handle XSRF for a CLI; proper session management is more complex.
XSRF_TOKEN_FILE = ".qoffee_cli_xsrf_token"

def get_base_url(args_base_url=None):
    """
    Gets base URL in order of precedence:
    1. Command-line argument (--base-url)
    2. Environment variable QOFFEE_BASE_URL
    3. DEFAULT_BASE_URL
    """
    if args_base_url and args_base_url != DEFAULT_BASE_URL: # If CLI arg is passed and is not the default itself
        return args_base_url
    return os.getenv("QOFFEE_BASE_URL", DEFAULT_BASE_URL)

def get_xsrf_token():
    """
    Placeholder for getting XSRF token.
    For robust CLI, this would need a proper way to login or retrieve from session.
    Currently, this is a very simplified approach: tries to read from a local file.
    The user might need to manually populate this file by inspecting browser cookies.
    """
    if os.path.exists(XSRF_TOKEN_FILE):
        with open(XSRF_TOKEN_FILE, 'r') as f:
            return f.read().strip()
    print(f"Warning: XSRF token file '{XSRF_TOKEN_FILE}' not found. POST requests might fail.")
    print(f"To make POST requests work, please log into QoffeeMaker via a browser,")
    print(f"inspect the '_xsrf' cookie value, and save it to a file named '{XSRF_TOKEN_FILE}' in this directory.")
    return None

def handle_response(response):
    """Prints formatted JSON response or error."""
    print(f"Status Code: {response.status_code}")
    try:
        print("Response JSON:")
        print(json.dumps(response.json(), indent=2))
    except json.JSONDecodeError:
        print("Response Text:")
        print(response.text)

def get_queue_status(args):
    """Fetches and displays the Home Connect queue status."""
    base_url = get_base_url(args.base_url)
    url = urljoin(base_url, "/api/hc/queue-status")
    print(f"Fetching queue status from {url}...")
    try:
        response = requests.get(url, timeout=10)
        handle_response(response)
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to QoffeeMaker API: {e}")

def retry_failed_command(args):
    """Retries a failed Home Connect command."""
    base_url = get_base_url(args.base_url)
    xsrf_token = get_xsrf_token()
    if not xsrf_token and not args.ignore_xsrf: # only proceed if token exists or user forces
        print("XSRF token needed for POST. Aborting.")
        return

    url = urljoin(base_url, "/api/hc/retry-failed-command")
    payload = {"command_index": args.index}
    headers = {}
    if xsrf_token:
        headers['X-XSRFToken'] = xsrf_token
        # Cookies might also be needed if the server validates them alongside XSRF token
        # headers['Cookie'] = f'_xsrf={xsrf_token}' # Example

    print(f"Attempting to retry command index {args.index} at {url}...")
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        handle_response(response)
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to QoffeeMaker API: {e}")

def delete_failed_command(args):
    """Deletes a failed Home Connect command."""
    base_url = get_base_url(args.base_url)
    xsrf_token = get_xsrf_token()
    if not xsrf_token and not args.ignore_xsrf:
        print("XSRF token needed for POST. Aborting.")
        return

    url = urljoin(base_url, "/api/hc/delete-failed-command")
    payload = {"command_index": args.index}
    headers = {}
    if xsrf_token:
        headers['X-XSRFToken'] = xsrf_token

    print(f"Attempting to delete command index {args.index} from failed queue at {url}...")
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        handle_response(response)
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to QoffeeMaker API: {e}")

def list_machines(args):
    """Lists Home Connect connected coffee machines."""
    base_url = get_base_url(args.base_url)
    url = urljoin(base_url, "/machines")
    print(f"Fetching machine list from {url}...")
    try:
        response = requests.get(url, timeout=10)
        handle_response(response)
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to QoffeeMaker API: {e}")

def get_health_status(args):
    """Fetches and displays the system health status."""
    base_url = get_base_url(args.base_url)
    url = urljoin(base_url, "/api/health")
    print(f"Fetching system health from {url}...")
    try:
        response = requests.get(url, timeout=10)
        handle_response(response)
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to QoffeeMaker API: {e}")


def main():
    parser = argparse.ArgumentParser(description="Qoffee-Maker Command Line Interface")
    parser.add_argument('--base-url', default=os.getenv("QOFFEE_BASE_URL", DEFAULT_BASE_URL),
                        help=f"Base URL of the QoffeeMaker Jupyter server (default: {DEFAULT_BASE_URL} or QOFFEE_BASE_URL env var)")

    subparsers = parser.add_subparsers(title="commands", dest="command", required=True)

    # Queue status command
    status_parser = subparsers.add_parser("status", help="Get Home Connect queue status.")
    status_parser.set_defaults(func=get_queue_status)

    # Retry command
    retry_parser = subparsers.add_parser("retry", help="Retry a failed Home Connect command.")
    retry_parser.add_argument("index", type=int, help="Index of the command in the failed queue to retry.")
    retry_parser.add_argument('--ignore-xsrf', action='store_true', help="Attempt POST without XSRF token (likely to fail).")
    retry_parser.set_defaults(func=retry_failed_command)

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a failed Home Connect command.")
    delete_parser.add_argument("index", type=int, help="Index of the command in the failed queue to delete.")
    delete_parser.add_argument('--ignore-xsrf', action='store_true', help="Attempt POST without XSRF token (likely to fail).")
    delete_parser.set_defaults(func=delete_failed_command)

    # List machines command
    machines_parser = subparsers.add_parser("list-machines", help="List connected Home Connect coffee machines.")
    machines_parser.set_defaults(func=list_machines)

    # Health check command
    health_parser = subparsers.add_parser("health", help="Get system health check status.")
    health_parser.set_defaults(func=get_health_status)

    args = parser.parse_args()

    # The get_base_url function now handles the args.base_url internally.
    # No need to modify global DEFAULT_BASE_URL here.

    args.func(args)

if __name__ == "__main__":
    main()
