#!/usr/bin/env python3
"""
Script to check the status of training jobs in Dropbox.

This script lists all trigger files in the Dropbox training_triggers folder
and checks their status to determine if training is in progress, completed, 
or failed.
"""

import os
import json
import datetime
import argparse
import requests
from pathlib import Path

def refresh_dropbox_token(app_key, app_secret, refresh_token):
    """Get a new access token using the refresh token."""
    token_url = "https://api.dropboxapi.com/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": app_key,
        "client_secret": app_secret
    }
    
    try:
        response = requests.post(token_url, data=data)
        if response.status_code == 200:
            token_data = response.json()
            return token_data["access_token"]
        else:
            print(f"Token refresh failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error refreshing token: {e}")
        return None

def list_trigger_files(access_token):
    """List all trigger files in the training_triggers folder."""
    list_url = "https://api.dropboxapi.com/2/files/list_folder"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "path": "/training_triggers",
        "recursive": False,
        "include_deleted": False
    }
    
    try:
        response = requests.post(list_url, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            result = response.json()
            return result.get("entries", [])
        else:
            print(f"Failed to list files: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"Error listing files: {e}")
        return []

def download_file(access_token, path):
    """Download a file from Dropbox."""
    download_url = "https://content.dropboxapi.com/2/files/download"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Dropbox-API-Arg": json.dumps({"path": path})
    }
    
    try:
        response = requests.post(download_url, headers=headers)
        if response.status_code == 200:
            return response.content
        else:
            print(f"Failed to download file: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error downloading file: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Check status of training jobs")
    parser.add_argument("--app-key", type=str, default=os.environ.get("DROPBOX_APP_KEY", "2bi422xpd3xd962"),
                      help="Dropbox app key")
    parser.add_argument("--app-secret", type=str, default=os.environ.get("DROPBOX_APP_SECRET", "j3yx0b41qdvfu86"),
                      help="Dropbox app secret")
    parser.add_argument("--refresh-token", type=str, 
                      default=os.environ.get("DROPBOX_REFRESH_TOKEN", "RvyL03RE5qAAAAAAAAAAAVMVebvE7jDx8Okd0ploMzr85c6txvCRXpJAt30mxrKF"),
                      help="Dropbox refresh token")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    args = parser.parse_args()
    
    # Refresh token to get access token
    access_token = refresh_dropbox_token(args.app_key, args.app_secret, args.refresh_token)
    if not access_token:
        print("Failed to get access token. Exiting.")
        return 1
    
    # List trigger files
    files = list_trigger_files(access_token)
    if not files:
        if args.json:
            print(json.dumps({"message": "No training jobs found", "jobs": []}))
        else:
            print("No training jobs found")
        return 0
    
    # Get status of each file
    jobs = []
    for file in files:
        if "training_needed" in file.get("name", ""):
            path = file.get("path_display")
            file_content = download_file(access_token, path)
            
            if file_content:
                try:
                    trigger_data = json.loads(file_content)
                    
                    # Add file metadata
                    trigger_data["file_path"] = path
                    trigger_data["file_name"] = file.get("name")
                    trigger_data["modified_at"] = file.get("server_modified")
                    
                    jobs.append(trigger_data)
                except json.JSONDecodeError:
                    print(f"Error decoding JSON from file: {path}")
    
    # Sort jobs by creation date (newest first)
    jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    # Output
    if args.json:
        print(json.dumps({"message": f"Found {len(jobs)} training jobs", "jobs": jobs}, indent=2))
    else:
        print(f"Found {len(jobs)} training jobs:")
        for i, job in enumerate(jobs):
            status = job.get("status", "unknown")
            created = job.get("created_at", "unknown")
            reason = job.get("reason", "unknown")
            
            status_emoji = {
                "pending": "⏳",
                "processing": "🔄",
                "training": "🏋️",
                "completed": "✅",
                "failed": "❌",
                "unknown": "❓"
            }.get(status, "❓")
            
            print(f"{i+1}. {status_emoji} {status.upper()} - Created: {created} - Reason: {reason}")
            
            if status == "completed" and "model_info" in job:
                model = job.get("model_info", {})
                print(f"   Model: {model.get('version', 'unknown')} - Accuracy: {model.get('accuracy', 0):.4f} - Date: {model.get('training_date', 'unknown')}")
            
            if "message" in job:
                print(f"   Message: {job.get('message')}")
            
            print()
    
    return 0

if __name__ == "__main__":
    exit(main())
