# Deploying to Render.com Using Docker

This guide provides instructions for deploying the Backdoor AI Learning Server to Render.com using Docker.

## Prerequisites

1. A [Render.com](https://render.com) account
2. A [Dropbox](https://dropbox.com) account 
3. Your Dropbox OAuth credentials (optional - defaults are provided in config.py)

## Deployment Steps

### 1. Prepare Your Repository

Your repository is already set up with:
- A Dockerfile that builds the Python 3.11 environment
- A configured render.yaml for Docker deployment
- A .dockerignore file to optimize the build
- entrypoint.sh script to handle startup

### 2. Create a New Web Service on Render

There are two ways to create your web service:

#### Option 1: Using the Dashboard (Recommended for First Deployment)

1. Log in to your Render.com dashboard
2. Click "New" and select "Web Service"
3. Connect your GitHub repository
4. Select the repository
5. Render will automatically detect the render.yaml file and use its configuration
6. Click "Create Web Service"

#### Option 2: Using the render.yaml File (For Advanced Users)

1. Create a "Blueprint" instance on Render
2. Connect to your repository
3. Render will use the render.yaml file to configure everything automatically

### 3. Environment Variables

The render.yaml file already includes these essential environment variables:

```
RENDER: true
MEMORY_ONLY_MODE: true
DROPBOX_ENABLED: true
PORT: 10000
STORAGE_MODE: dropbox
MEMORY_OPTIMIZED: true
USE_DROPBOX_STREAMING: true
NO_LOCAL_STORAGE: true
GUNICORN_WORKERS: 2
```

#### Optional: Custom Dropbox Credentials

If you want to use your own Dropbox app instead of the default one:

1. Create a Dropbox app at https://www.dropbox.com/developers/apps
2. Add these additional environment variables in the Render dashboard:
   - DROPBOX_APP_KEY - Your Dropbox app key
   - DROPBOX_APP_SECRET - Your Dropbox app secret
   - DROPBOX_REFRESH_TOKEN - Your Dropbox refresh token

### 4. Monitor Deployment

1. Render will build the Docker image and deploy your application
2. Monitor the build logs for any errors
3. Once deployed, your application will be accessible at `https://your-app-name.onrender.com`

### 5. Verify Dropbox Integration

After deployment:

1. Visit `https://your-app-name.onrender.com/health` to check if the service is running correctly
2. Check if "dropbox_status" shows "connected" in the health check
3. If Dropbox shows "disconnected", you may need to set up OAuth:
   - Visit `https://your-app-name.onrender.com/oauth/dropbox/authorize`
   - Follow the authorization flow
   - After authorization, the tokens will be automatically saved

## Troubleshooting

### Dropbox Authentication Issues

If you encounter problems with Dropbox authentication:

1. Check the logs for specific error messages
2. Verify that your Dropbox app has the correct permissions
3. Try using your own Dropbox credentials by adding them as environment variables

### Container Resource Issues

If your application crashes due to memory limits:

1. Upgrade to a higher-tier plan on Render
2. Adjust GUNICORN_WORKERS to a lower value (e.g., 1)
3. Ensure MEMORY_OPTIMIZED is set to "true"

### Port Binding Issues

If you see "address already in use" errors:

1. Ensure PORT is set to 10000 in environment variables
2. Check that the Dockerfile exposes port 10000
3. Verify that entrypoint.sh starts the server on port 10000

## Maintenance

### Updating Your Deployment

To update your application:

1. Push changes to your repository
2. Render will automatically rebuild and deploy the new version

### Checking Logs

Access logs through the Render dashboard:

1. Select your web service
2. Click on "Logs" in the left sidebar
3. Use the filter options to find specific messages

### Monitoring Health

Set up monitoring:

1. Use the `/health` endpoint to check application status
2. Set up alerts in Render for any downtime
3. Consider adding custom monitoring with tools like UptimeRobot
