# Google Colab Integration for Backdoor AI Training

This integration allows you to offload model training from your Render.com Flask application to Google Colab, leveraging free GPU/TPU resources for more efficient training.

## Overview

The Backdoor AI system uses a sophisticated model training system that can be resource-intensive. This integration moves the training to Google Colab while keeping the API service running on Render.com.

### Architecture

1. **Render.com Flask App**: 
   - Collects user interactions and model uploads
   - Serves trained models to clients
   - Stores data in Dropbox

2. **Dropbox Storage**:
   - Acts as the shared data layer between Render and Colab
   - Stores interaction data, user-uploaded models, trained models

3. **Google Colab**:
   - Performs resource-intensive model training
   - Accesses training data from Dropbox
   - Saves trained models back to Dropbox

## Files in this Integration

- `backdoor_ai_trainer.ipynb` - Google Colab notebook for model training
- `create_training_trigger.py` - Script to create trigger files in Dropbox
- `get_training_status.py` - Script to check the status of training jobs
- `../app_trigger_training.py` - Flask app integration script

## Setup Instructions

### 1. Dropbox Configuration

Ensure your Render app has the correct Dropbox credentials configured:
- `DROPBOX_APP_KEY` 
- `DROPBOX_APP_SECRET`
- `DROPBOX_REFRESH_TOKEN`

The Colab notebook will use the same credentials to access your Dropbox.

### 2. Trigger File Configuration

Create a folder in your Dropbox app folder called `training_triggers`:

```
/training_triggers/
```

### 3. Colab Notebook Setup

1. Upload the `backdoor_ai_trainer.ipynb` notebook to Google Colab
2. Update the Dropbox credentials in the notebook if they're different from the defaults
3. Run the notebook cells to install dependencies and set up the environment

### 4. Triggering the Training Process

#### Option 1: Using the app_trigger_training.py Script (from Flask app)

This script integrates with the Flask app and can be triggered programmatically:

```python
from app_trigger_training import create_trigger_file

# Trigger training with a reason
create_trigger_file(reason="new_models", force=False)
```

Or from the command line:

```bash
python app_trigger_training.py --reason "new_interactions" --force
```

#### Option 2: Using the create_training_trigger.py Script (standalone)

This script can be used from any environment with the Dropbox credentials:

```bash
python colab_integration/create_training_trigger.py --reason "manual_trigger" --force
```

#### Option 3: Manual Execution in Colab

1. Open the Google Colab notebook
2. Enter your Dropbox credentials
3. Run all cells to execute the training process
4. The notebook will check for pending models and perform training if needed

### 5. Checking Training Status

Use the get_training_status.py script to check on training progress:

```bash
python colab_integration/get_training_status.py
```

For JSON output (useful for automated systems):

```bash
python colab_integration/get_training_status.py --json > status.json
```

## How the Integration Works

### Trigger Mechanism

The system uses a simple file-based trigger mechanism:

1. Your Render app writes a trigger file (`training_needed.json`) to Dropbox when:
   - A sufficient number of user-uploaded models are pending
   - Enough new interaction data has been collected
   - A manual training is requested

2. The Colab notebook checks for trigger files when run
   - If a trigger is found, training begins
   - If no trigger is found, it checks if training is needed based on the same criteria as the Render app

### Training Process

The Colab notebook implements the same `IntentClassifier` training logic that exists in the Render app:

1. **Data Collection**:
   - Download interaction data from Dropbox
   - Retrieve pending user-uploaded models

2. **Model Training**:
   - Preprocess text data
   - Extract features
   - Train the base classifier (RandomForest)
   - Create ensemble model with user-uploaded models
   - Convert to CoreML format

3. **Model Storage**:
   - Save trained model back to Dropbox
   - Update model version info
   - Create training summary

### Status Notification

After training completes:
1. The notebook updates the trigger file with the result status
2. The notebook creates a training report markdown file in Dropbox
3. The Render app can detect the new model and start using it automatically

## Troubleshooting

If the training process fails:

1. Check the Colab notebook execution logs
2. Verify Dropbox access is working correctly
3. Ensure there's sufficient training data available
4. Check that your user-uploaded models are compatible with the expected format

## Schedule Options

For ongoing automation:

1. **Manual Schedule**: Open and run the notebook when needed
2. **Colab Pro Features**: Use Colab's background execution (Pro feature)
3. **Regular Schedule**: Set up a simple script to open and execute the notebook on a schedule