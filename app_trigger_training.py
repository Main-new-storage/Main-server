#!/usr/bin/env python3
"""
Script to trigger model training on Google Colab from the Render app.

This script creates a trigger file in Dropbox that signals to Google Colab
that a new model training session is needed. It integrates with the Backdoor AI
application to automatically trigger training based on app criteria.
"""

import os
import json
import argparse
import sys
import datetime
from pathlib import Path

def create_trigger_file(reason="app_trigger", force=False):
    """Create a training trigger file in Dropbox."""
    try:
        # Import app configuration to get Dropbox credentials
        import config
        from utils.storage_factory import get_storage
        
        # Get storage
        storage = get_storage()
        
        # Create trigger data
        trigger_data = {
            "created_at": datetime.datetime.now().isoformat(),
            "reason": reason,
            "force": force,
            "status": "pending",
            "source": "render_app",
            "triggered_by": "app_script"
        }
        
        # Generate filename
        filename = f"training_needed_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        folder = "training_triggers"
        
        # Ensure trigger folder exists
        try:
            from utils.dropbox_storage import get_dropbox_storage
            dropbox_storage = get_dropbox_storage()
            try:
                dropbox_storage.dbx.files_get_metadata(f"/{folder}")
            except Exception:
                # Create folder if it doesn't exist
                dropbox_storage.dbx.files_create_folder_v2(f"/{folder}")
                print(f"Created {folder} folder in Dropbox")
        except Exception as e:
            print(f"Error ensuring folder exists: {e}")
        
        # Convert trigger data to bytes
        trigger_json = json.dumps(trigger_data)
        trigger_bytes = trigger_json.encode('utf-8')
        
        # Create in-memory file buffer
        import io
        trigger_buffer = io.BytesIO(trigger_bytes)
        
        # Upload to Dropbox
        upload_result = storage.upload_model(
            data_or_path=trigger_buffer,
            model_name=filename,
            folder=folder
        )
        
        if upload_result.get('success', False):
            print(f"Trigger file created successfully: {upload_result.get('path')}")
            return True
        else:
            print(f"Failed to create trigger file: {upload_result.get('error', 'Unknown error')}")
            return False
            
    except ImportError as ie:
        print(f"Import error - not running in app context? {ie}")
        return False
    except Exception as e:
        print(f"Error creating trigger file: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Trigger model training on Google Colab from Render app")
    parser.add_argument("--reason", type=str, default="app_trigger", 
                      help="Reason for triggering training")
    parser.add_argument("--force", action="store_true", 
                      help="Force training even if criteria not met")
    
    args = parser.parse_args()
    
    success = create_trigger_file(args.reason, args.force)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
