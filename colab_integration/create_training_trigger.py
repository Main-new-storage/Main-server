#!/usr/bin/env python3
"""
Script to create a training trigger file in Dropbox.

This script creates a trigger file in the Dropbox training_triggers folder
that signals to Google Colab that a new model training session is needed.
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

def create_trigger_file(access_token, trigger_data):
    """Create a trigger file in Dropbox."""
    upload_url = "https://content.dropboxapi.com/2/files/upload"
    
    # Convert trigger data to JSON string
    trigger_json = json.dumps(trigger_data)
    
    # Create file path
    path = f"/training_triggers/training_needed_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Prepare headers
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Dropbox-API-Arg": json.dumps({
            "path": path,
            "mode": "add",
            "autorename": True,
            "mute": False
        }),
        "Content-Type": "application/octet-stream"
    }
    
    # Upload file
    try:
        response = requests.post(upload_url, headers=headers, data=trigger_json.encode('utf-8'))
        if response.status_code == 200:
            print(f"Trigger file created successfully at: {path}")
            return True
        else:
            print(f"Failed to create trigger file: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Error creating trigger file: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Create a training trigger file in Dropbox")
    parser.add_argument("--reason", type=str, default="manual_trigger", 
                      help="Reason for triggering training")
    parser.add_argument("--force", action="store_true", 
                      help="Force training even if criteria not met")
    parser.add_argument("--app-key", type=str, default=os.environ.get("DROPBOX_APP_KEY", "2bi422xpd3xd962"),
                      help="Dropbox app key")
    parser.add_argument("--app-secret", type=str, default=os.environ.get("DROPBOX_APP_SECRET", "j3yx0b41qdvfu86"),
                      help="Dropbox app secret")
    parser.add_argument("--refresh-token", type=str, 
                      default=os.environ.get("DROPBOX_REFRESH_TOKEN", "RvyL03RE5qAAAAAAAAAAAVMVebvE7jDx8Okd0ploMzr85c6txvCRXpJAt30mxrKF"),
                      help="Dropbox refresh token")
    
    args = parser.parse_args()
    
    # Refresh token to get access token
    access_token = refresh_dropbox_token(args.app_key, args.app_secret, args.refresh_token)
    if not access_token:
        print("Failed to get access token. Exiting.")
        return 1
    
    # Create trigger data
    trigger_data = {
        "created_at": datetime.datetime.now().isoformat(),
        "reason": args.reason,
        "force": args.force,
        "status": "pending",
        "source": "api",
        "triggered_by": os.environ.get("USER", "unknown")
    }
    
    # Create trigger file
    success = create_trigger_file(access_token, trigger_data)
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
