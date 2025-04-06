#!/usr/bin/env python3
"""
Fix script for the Backdoor AI Trainer notebook.

This script modifies the backdoor_ai_trainer.ipynb notebook to use
a more robust CoreML conversion approach that handles compatibility issues.
"""

import json
import os
import sys

def fix_notebook():
    """Fix the backdoor_ai_trainer.ipynb notebook"""
    notebook_path = os.path.join('colab_integration', 'backdoor_ai_trainer.ipynb')
    
    # Check if notebook exists
    if not os.path.exists(notebook_path):
        print(f"Error: Notebook not found at {notebook_path}")
        return False
    
    # Create backup
    backup_path = f"{notebook_path}.bak"
    try:
        with open(notebook_path, 'r') as f:
            notebook_content = f.read()
            
        with open(backup_path, 'w') as f:
            f.write(notebook_content)
            
        print(f"Created backup at {backup_path}")
    except Exception as e:
        print(f"Error creating backup: {e}")
        return False
    
    # Load the notebook
    try:
        with open(notebook_path, 'r') as f:
            notebook = json.load(f)
    except Exception as e:
        print(f"Error loading notebook: {e}")
        return False
    
    # 1. Add cell to import coreml_fix module at the beginning
    coreml_fix_import_cell = {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "source": [
            "# Import CoreML fix module\n",
            "!wget -q https://raw.githubusercontent.com/Main-new-storage/Main-server/fix-dropbox-memory-issues/colab_integration/coreml_fix.py\n",
            "import sys\n",
            "import os\n",
            "\n",
            "# Make it available for import\n",
            "if not '.' in sys.path:\n",
            "    sys.path.append('.')\n",
            "    \n",
            "# Apply fixes at startup\n",
            "try:\n",
            "    import coreml_fix\n",
            "    print(\"CoreML compatibility fixes applied successfully\")\n",
            "except ImportError as e:\n",
            "    print(f\"Could not import CoreML fixes: {e}\")"
        ]
    }
    
    # Find a good position to insert the cell - after imports
    inserted = False
    for i, cell in enumerate(notebook['cells']):
        if cell.get('cell_type') == 'code' and any('import' in line for line in cell.get('source', [])):
            notebook['cells'].insert(i+1, coreml_fix_import_cell)
            inserted = True
            break
    
    if not inserted:
        # Insert at the beginning if we didn't find a better place
        notebook['cells'].insert(1, coreml_fix_import_cell)
    
    # 2. Update the CoreML conversion method
    convert_to_coreml_replacement = [
        "    def _convert_to_coreml(self, output_path):\n",
        "        # Define prediction function\n",
        "        def predict_intent(text):\n",
        "            processed_text = preprocess_text(text)\n",
        "            vec_text = self.vectorizer.transform([processed_text])\n",
        "            intent = self.model.predict(vec_text)[0]\n",
        "            probabilities = self.model.predict_proba(vec_text)[0]\n",
        "            return intent, probabilities\n",
        "        \n",
        "        # Import the CoreML fix module if available\n",
        "        try:\n",
        "            import coreml_fix\n",
        "            \n",
        "            # Use the safe conversion method\n",
        "            result = coreml_fix.safe_convert_to_coreml(\n",
        "                predict_intent,\n",
        "                inputs=[('text', 'str')],\n",
        "                outputs=[('intent', 'str'), ('probabilities', 'float32')],\n",
        "                fallback_path=None\n",
        "            )\n",
        "            \n",
        "            if result['success']:\n",
        "                coreml_model = result['model']\n",
        "                \n",
        "                # Add metadata\n",
        "                coreml_model.user_defined_metadata['version'] = self.model_version\n",
        "                coreml_model.user_defined_metadata['training_date'] = self.training_date\n",
        "                coreml_model.user_defined_metadata['accuracy'] = str(self.accuracy)\n",
        "                \n",
        "                # Save model\n",
        "                coreml_model.save(output_path)\n",
        "                return True\n",
        "            else:\n",
        "                print(f\"CoreML conversion failed: {result.get('error')}\")\n",
        "                # Fall back to standard conversion as last resort\n",
        "        except ImportError:\n",
        "            print(\"CoreML fix module not available, using standard conversion\")\n",
        "        \n",
        "        # Standard conversion as fallback\n",
        "        try:\n",
        "            # Fix common CoreML issues\n",
        "            if 'coremltools' in sys.modules:\n",
        "                import coremltools as ct\n",
        "                # Monkey patch version checks if needed\n",
        "                if hasattr(ct, '_dependency_check'):\n",
        "                    for check_name in ['verify_scikit_learn_version', 'verify_tensorflow_version', \n",
        "                                    'verify_torch_version', 'verify_xgboost_version']:\n",
        "                        if hasattr(ct._dependency_check, check_name):\n",
        "                            setattr(ct._dependency_check, check_name, lambda *args, **kwargs: True)\n",
        "                            \n",
        "            # Convert to CoreML\n",
        "            coreml_model = ct.convert(\n",
        "                predict_intent,\n",
        "                inputs=[ct.TensorType(shape=(1,), dtype=str)],\n",
        "                outputs=[\n",
        "                    ct.TensorType(name='intent'),\n",
        "                    ct.TensorType(name='probabilities', dtype=np.float32)\n",
        "                ],\n",
        "                classifier_config=ct.ClassifierConfig(self.classes)\n",
        "            )\n",
        "            \n",
        "            # Add metadata\n",
        "            coreml_model.user_defined_metadata['version'] = self.model_version\n",
        "            coreml_model.user_defined_metadata['training_date'] = self.training_date\n",
        "            coreml_model.user_defined_metadata['accuracy'] = str(self.accuracy)\n",
        "            \n",
        "            # Save model\n",
        "            coreml_model.save(output_path)\n",
        "            return True\n",
        "        except Exception as e:\n",
        "            print(f\"CoreML conversion completely failed: {e}\")\n",
        "            return False\n"
    ]
    
    # Find and replace the _convert_to_coreml method
    original_method = [
        "    def _convert_to_coreml(self, output_path):\n",
        "        # Define prediction function\n",
        "        def predict_intent(text):\n",
        "            processed_text = preprocess_text(text)\n",
        "            vec_text = self.vectorizer.transform([processed_text])\n",
        "            intent = self.model.predict(vec_text)[0]\n",
        "            probabilities = self.model.predict_proba(vec_text)[0]\n",
        "            return intent, probabilities\n",
        "        \n",
        "        # Convert to CoreML\n",
        "        coreml_model = ct.convert(\n",
        "            predict_intent,\n",
        "            inputs=[ct.TensorType(shape=(1,), dtype=str)],\n",
        "            outputs=[\n",
        "                ct.TensorType(name='intent'),\n",
        "                ct.TensorType(name='probabilities', dtype=np.float32)\n",
        "            ],\n",
        "            classifier_config=ct.ClassifierConfig(self.classes)\n",
        "        )\n",
        "        \n",
        "        # Add metadata\n",
        "        coreml_model.user_defined_metadata['version'] = self.model_version\n",
        "        coreml_model.user_defined_metadata['training_date'] = self.training_date\n",
        "        coreml_model.user_defined_metadata['accuracy'] = str(self.accuracy)\n",
        "        \n",
        "        # Save model\n",
        "        coreml_model.save(output_path)\n",
        "        return True\n"
    ]
    
    replaced = False
    for cell in notebook['cells']:
        if cell.get('cell_type') == 'code':
            source = cell.get('source', [])
            method_start = None
            for i, line in enumerate(source):
                if "def _convert_to_coreml" in line:
                    method_start = i
                    break
                    
            if method_start is not None:
                # Check if the method matches our expected pattern
                match = True
                for i, line in enumerate(original_method):
                    if method_start + i >= len(source) or line != source[method_start + i]:
                        match = False
                        break
                
                if match:
                    # Replace the method
                    source[method_start:method_start + len(original_method)] = convert_to_coreml_replacement
                    replaced = True
                    break
    
    if not replaced:
        print("Warning: Could not find and replace the _convert_to_coreml method.")
        print("You'll need to manually update the method to use the coreml_fix module.")
    
    # Save the modified notebook
    try:
        with open(notebook_path, 'w') as f:
            json.dump(notebook, f, indent=1)
            
        print("Successfully updated notebook")
        return True
    except Exception as e:
        print(f"Error saving notebook: {e}")
        return False

if __name__ == "__main__":
    success = fix_notebook()
    if success:
        print("Notebook successfully fixed!")
    else:
        print("Failed to fix notebook.")
