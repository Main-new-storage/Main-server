# Deploying Backdoor AI Learning Server on Glitch.com

This README provides instructions for deploying the Backdoor AI Learning Server on Glitch.com.

## Quick Setup

This project includes hardcoded Dropbox credentials, so you can deploy it immediately without additional configuration. The application will automatically authenticate with Dropbox using the built-in refresh token.

## Prerequisites

1. A Glitch.com account

## Setup Steps

### 1. Import this project to Glitch

1. Create a new Glitch project
2. Import this repository or upload the files

### 2. Everything is pre-configured

The project includes:
- Pre-configured Dropbox credentials
- Automatic token refresh
- Memory-only mode optimization for Glitch

No additional configuration is needed - the app will start automatically with the preconfigured settings.

### 3. Prepare Dropbox Storage (Only if needed)

The app will attempt to create these folders in Dropbox automatically, but you can create them manually if needed:
- `backdoor_models`
- `nltk_data`
- `base_model`

### 4. Deploy Base Model (If you have one)

If you have a CoreML model (.mlmodel file):
1. Rename it to `model_1.0.0.mlmodel`
2. Upload it to the `base_model` folder in your Dropbox app folder

## Usage

Once running, your API is available at:
- `https://your-project-name.glitch.me/api/ai/learn` - Submit learning data
- `https://your-project-name.glitch.me/api/ai/upload-model` - Upload models
- `https://your-project-name.glitch.me/api/ai/models/{version}` - Download models

## Handling Sleep Mode

Glitch free tier projects go to sleep after 5 minutes of inactivity. When the project wakes up:

1. It will automatically reinitialize and reconnect to Dropbox
2. Any pending data will be synchronized

## Custom Configuration (Optional)

If you want to use your own Dropbox app:

1. Create a Dropbox app at https://www.dropbox.com/developers/apps
2. Choose "App folder" access 
3. Set the OAuth2 redirect URI to `https://your-project-name.glitch.me/oauth/dropbox/callback`
4. In the Glitch.com project settings, update these environment variables:
   - `DROPBOX_APP_KEY`: Your Dropbox app key
   - `DROPBOX_APP_SECRET`: Your Dropbox app secret
   - `DROPBOX_REFRESH_TOKEN`: Your Dropbox refresh token

## Troubleshooting

- Check logs in the Glitch console
- Verify the app has connected to Dropbox successfully
- Ensure proper folders exist in Dropbox
