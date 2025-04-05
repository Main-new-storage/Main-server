# Setting Up Your Glitch-Hosted Backdoor AI Server

This guide walks you through the complete setup process for the Backdoor AI Learning Server on Glitch.com.

## Step 1: Create a Dropbox App

1. Go to [Dropbox App Console](https://www.dropbox.com/developers/apps)
2. Click "Create App"
3. Select "Scoped access"
4. Choose "App folder" access
5. Name your app (e.g., "BackdoorAIServer")
6. In the settings, add a redirect URI: `https://your-glitch-project-name.glitch.me/oauth/dropbox/callback`
7. Note your App Key and App Secret
8. Under "Permissions", enable:
   - files.metadata.read
   - files.metadata.write
   - files.content.read
   - files.content.write

## Step 2: Set Up Your Glitch Project

1. Go to [Glitch.com](https://glitch.com/)
2. Click "New Project" → "Import from GitHub"
3. Enter the repository URL
4. Once imported, go to your project settings (click the Tools button)
5. Under "Environment Variables" add:
   - `DROPBOX_APP_KEY`: Your Dropbox app key
   - `DROPBOX_APP_SECRET`: Your Dropbox app secret

## Step 3: Get Dropbox Authorization

1. After your project is running, visit:
   `https://your-glitch-project-name.glitch.me/oauth/dropbox/authorize`
2. Log in to your Dropbox account and authorize the app
3. The refresh token will be automatically stored in your project

## Step 4: Create Required Folders in Dropbox

After authorization, the app will attempt to create these folders automatically. If they aren't created, you can create them manually in your Dropbox app folder:

1. `backdoor_models`
2. `nltk_data`
3. `base_model`

## Step 5: Upload Base Model (If Available)

If you have a CoreML model (.mlmodel file):
1. Rename it to `model_1.0.0.mlmodel`
2. Upload it to the `base_model` folder in your Dropbox app folder

## Step 6: Verify Installation

Your API endpoints will be available at:
- `https://your-glitch-project-name.glitch.me/api/ai/learn`
- `https://your-glitch-project-name.glitch.me/api/ai/upload-model`
- `https://your-glitch-project-name.glitch.me/api/ai/models/{version}`

## Troubleshooting

If you encounter issues:

1. **Connection failures**: 
   - Check the logs in the Glitch console
   - Verify Dropbox credentials are correct
   - Ensure the refresh token was generated correctly

2. **Memory limitations**:
   - Reduce `GUNICORN_WORKERS` to 1 in .env
   - Disable unnecessary features

3. **Project sleeping**:
   - Glitch free tier projects sleep after 5 minutes of inactivity
   - Consider upgrading to a paid plan or use a ping service

4. **Model not found**:
   - Verify the base model is in the correct folder
   - Check folder permissions in your Dropbox app

## Upgrading to Avoid Sleep

For production use, consider one of these options:
1. Upgrade to Glitch Pro to avoid project sleep
2. Use a service like UptimeRobot to ping your app regularly
3. Consider migrating to Render or Koyeb for production needs
