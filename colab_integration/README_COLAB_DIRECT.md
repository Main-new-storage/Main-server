# Direct Colab Notebook for Backdoor AI Training

This directory contains a standalone notebook for training Backdoor AI models in Google Colab.

## Updated Notebook: `backdoor_ai_trainer_direct.ipynb`

The `backdoor_ai_trainer_direct.ipynb` is a simplified and fixed version of the original trainer that addresses several compatibility and dependency issues. It's designed to work consistently in Google Colab without relying on external helper scripts.

### What's Fixed

1. **Package Installation**:
   - Uses scikit-learn 1.1.3 with binary wheels instead of 1.5.1 that failed to build
   - Installs protobuf 3.20.3 explicitly to avoid conflicts
   - Properly installs coremltools 6.3

2. **CoreML Compatibility**:
   - Includes patches for coremltools version checks
   - Adds code to handle missing libcoremlpython module
   - Provides fallback methods for model conversion

3. **Dropbox Integration**:
   - Properly imports WriteMode from dropbox.files
   - Ensures all required Dropbox folders exist, including NLTK folders
   - Robust folder existence checks with proper error handling

4. **Extra Features**:
   - Package version verification
   - More detailed error logging
   - Better exception handling

### How to Use

1. **Open in Google Colab**:
   - Upload the notebook to your Google Drive
   - Open with Google Colab

2. **Run All Cells Sequentially**:
   - The notebook will install dependencies, connect to Dropbox, and set up the environment

3. **Optional Configuration**:
   - Edit the Dropbox credentials if needed
   - Adjust training parameters as desired

4. **Troubleshooting**:
   - If you encounter any issues, check the verification cell output
   - The notebook includes comprehensive error handling and fallback mechanisms

### Differences from Original Notebook

This notebook consolidates code that was previously spread across multiple files and includes fixes for:

- The `NameError: name 'null' is not defined` error
- Missing library errors with coremltools
- Dependency conflicts with scikit-learn and protobuf
- Dropbox folder creation issues

### Maintenance

When you need to update the notebook in the future:

1. Make changes directly in this notebook rather than using helper scripts
2. Maintain the fixes for package versions and compatibility
3. Keep the error handling and verification sections

This direct approach allows for easier debugging and maintenance without relying on external tools or helper scripts.
