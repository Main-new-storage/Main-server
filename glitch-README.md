# Deploying Backdoor AI Learning Server on Glitch.com

This README provides instructions for deploying the Backdoor AI Learning Server on Glitch.com.

## Prerequisites

1. A Dropbox account and API app
2. A Glitch.com account

## Setup Steps

### 1. Set up your Dropbox App

1. Create a Dropbox app at https://www.dropbox.com/developers/apps
2. Choose "App folder" access
3. Set the OAuth2 redirect URI to `https://your-project-name.glitch.me/oauth/dropbox/callback`
4. Note your App Key and App Secret

### 2. Import this project to Glitch

1. Create a new Glitch project
2. Import this repository or upload the files

### 3. Set Environment Variables

Add these required environment variables in the Glitch.com project settings:

- `DROPBOX_APP_KEY`: Your Dropbox app key
- `DROPBOX_APP_SECRET`: Your Dropbox app secret
- `DROPBOX_REFRESH_TOKEN`: Your Dropbox refresh token (see instructions below)

### 4. Generate a Refresh Token

After setting up your project on Glitch:

1. Visit `https://your-project-name.glitch.me/oauth/dropbox/authorize`
2. Log in to Dropbox and grant access
3. The refresh token will be automatically set in your project

Alternatively, run the `add_refresh_token.py` script locally:

```bash
python add_refresh_token.py
```

### 5. Prepare Dropbox Storage

Create these folders in your Dropbox app folder:
- `backdoor_models`
- `nltk_data`
- `base_model`

### 6. Deploy Base Model

If you have a CoreML model (.mlmodel file):
1. Rename it to `model_1.0.0.mlmodel`
2. Upload it to the `base_model` folder in your Dropbox app folder

## Usage

Once set up, your API is available at:
- `https://your-project-name.glitch.me/api/ai/learn` - Submit learning data
- `https://your-project-name.glitch.me/api/ai/upload-model` - Upload models
- `https://your-project-name.glitch.me/api/ai/models/{version}` - Download models

## Handling Sleep Mode

Glitch free tier projects go to sleep after 5 minutes of inactivity. When the project wakes up:

1. It will automatically reinitialize and reconnect to Dropbox
2. Any pending data will be synchronized

## Troubleshooting

- Check logs in the Glitch console
- Verify Dropbox tokens are valid
- Ensure proper folders exist in Dropbox
