// Pre-start script for Glitch to ensure Dropbox token refresh happens automatically

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Create the dropbox_tokens.json file if it doesn't exist
const tokenFile = path.join(__dirname, 'dropbox_tokens.json');
const refreshToken = process.env.DROPBOX_REFRESH_TOKEN || 'RvyL03RE5qAAAAAAAAAAAVMVebvE7jDx8Okd0ploMzr85c6txvCRXpJAt30mxrKF';
const appKey = process.env.DROPBOX_APP_KEY || '2bi422xpd3xd962';
const appSecret = process.env.DROPBOX_APP_SECRET || 'j3yx0b41qdvfu86';

// Create token file with hardcoded credentials if it doesn't exist
if (!fs.existsSync(tokenFile)) {
  console.log('Creating Dropbox token file...');
  
  const tokenData = {
    refresh_token: refreshToken,
    app_key: appKey,
    app_secret: appSecret,
    created_at: new Date().toISOString()
  };
  
  try {
    fs.writeFileSync(tokenFile, JSON.stringify(tokenData, null, 2));
    console.log('Created Dropbox token file successfully');
  } catch (err) {
    console.error('Error creating token file:', err);
  }
} else {
  console.log('Dropbox token file already exists');
  
  // Update token file with latest values from environment if available
  try {
    const tokenData = JSON.parse(fs.readFileSync(tokenFile, 'utf8'));
    let updated = false;
    
    if (process.env.DROPBOX_REFRESH_TOKEN && tokenData.refresh_token !== process.env.DROPBOX_REFRESH_TOKEN) {
      tokenData.refresh_token = process.env.DROPBOX_REFRESH_TOKEN;
      updated = true;
    }
    
    if (updated) {
      tokenData.updated_at = new Date().toISOString();
      fs.writeFileSync(tokenFile, JSON.stringify(tokenData, null, 2));
      console.log('Updated token file with latest values');
    }
  } catch (err) {
    console.error('Error updating token file:', err);
  }
}

// Remind about token setup
console.log('Dropbox tokens configured. App will use these to authenticate automatically.');

// End message
console.log('Glitch pre-start setup completed successfully');
