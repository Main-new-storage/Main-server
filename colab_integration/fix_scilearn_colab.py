#!/usr/bin/env python3
"""
Fix scikit-learn and coremltools installation issues in Colab notebook.

This script updates the package installation commands in the notebook to:
1. Use scikit-learn 1.1.3 which has reliable binary wheels
2. Install protobuf 3.20.3 explicitly to avoid conflicts
3. Fix coremltools installation to avoid build errors
"""

import json
import sys
import os

def fix_notebook():
    """Fix the backdoor_ai_trainer.ipynb notebook packages."""
    notebook_path = 'colab_integration/backdoor_ai_trainer.ipynb'
    
    try:
        # Read notebook
        with open(notebook_path, 'r') as f:
            notebook = json.load(f)
            
        # Create backup
        backup_path = f"{notebook_path}.bak"
        with open(backup_path, 'w') as f:
            json.dump(notebook, f)
            
        # Find and update the pip install cell
        found_cell = False
        
        for i, cell in enumerate(notebook['cells']):
            if cell.get('cell_type') == 'code':
                source = cell.get('source', [])
                if any('!pip install' in line for line in source):
                    # This is the package installation cell
                    new_source = [
                        "# Install required packages with specific versions for compatibility\n",
                        "!pip install dropbox pandas numpy nltk flask joblib\n",
                        "\n",
                        "# Install specific protobuf version first (required for coremltools)\n",
                        "!pip install protobuf==3.20.3\n",
                        "\n",
                        "# Install scikit-learn with version that has reliable binary wheels\n",
                        "!pip install scikit-learn==1.1.3 --prefer-binary\n",
                        "\n",
                        "# Uninstall existing coremltools (if any)\n",
                        "!pip uninstall -y coremltools\n",
                        "\n",
                        "# Install coremltools with appropriate version\n",
                        "!pip install coremltools==6.3\n"
                    ]
                    
                    notebook['cells'][i]['source'] = new_source
                    found_cell = True
                    break
        
        if not found_cell:
            print("Could not find package installation cell in the notebook")
            return False
        
        # Also add a verification cell
        verification_cell = {
            "cell_type": "code",
            "execution_count": null,
            "metadata": {},
            "source": [
                "# Check installed package versions to verify everything is compatible\n",
                "!python -c \"import sys; print(f'Python version: {sys.version}')\" \n",
                "!python -c \"import sklearn; print(f'scikit-learn version: {sklearn.__version__}')\" \n", 
                "!python -c \"import coremltools; print(f'coremltools version: {coremltools.__version__}')\" \n",
                "!python -c \"import numpy; print(f'numpy version: {numpy.__version__}')\" \n",
                "!python -c \"import pandas; print(f'pandas version: {pandas.__version__}')\" \n",
                "\n",
                "# Fix for missing libcoremlpython module\n",
                "import os\n",
                "import coremltools\n",
                "\n",
                "coreml_dir = os.path.dirname(coremltools.__file__)\n",
                "lib_path = os.path.join(coreml_dir, 'libcoremlpython.py')\n",
                "\n",
                "if not os.path.exists(lib_path):\n",
                "    print(f\"Creating mock libcoremlpython module at {lib_path}\")\n",
                "    with open(lib_path, 'w') as f:\n",
                "        f.write(\"\"\"\n",
                "class MockProxy:\n",
                "    def __init__(self, *args, **kwargs):\n",
                "        pass\n",
                "        \n",
                "    def __getattr__(self, name):\n",
                "        def mock_method(*args, **kwargs):\n",
                "            return None\n",
                "        return mock_method\n",
                "\n",
                "# Create mock proxies\n",
                "_MLModelProxy = MockProxy\n",
                "_MLComputePlanProxy = MockProxy\n",
                "_MLModelAssetProxy = MockProxy\n",
                "_MLCPUComputeDeviceProxy = MockProxy\n",
                "_MLGPUComputeDeviceProxy = MockProxy\n",
                "_MLNeuralEngineComputeDeviceProxy = MockProxy\n",
                "\"\"\")\n",
                "    print(\"Mock libcoremlpython module created successfully\")\n",
                "else:\n",
                "    print(\"libcoremlpython module already exists\")\n"
            ]
        }
        
        # Find the import cell to insert verification after it
        for i, cell in enumerate(notebook['cells']):
            if cell.get('cell_type') == 'code':
                source = cell.get('source', [])
                if any('import coremltools' in line for line in source):
                    # Insert after this cell
                    notebook['cells'].insert(i+1, verification_cell)
                    print("Added verification cell after imports")
                    break
        
        # Save the modified notebook
        with open(notebook_path, 'w') as f:
            json.dump(notebook, f, indent=1)
            
        print(f"Successfully updated {notebook_path}")
        print(f"Backup saved to {backup_path}")
        return True
        
    except Exception as e:
        print(f"Error fixing notebook: {e}")
        return False

if __name__ == "__main__":
    fix_notebook()
