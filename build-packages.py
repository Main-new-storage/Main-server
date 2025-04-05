#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to install packages in the correct order with appropriate flags.
This script helps resolve dependency issues on platforms like Render.com
"""

import subprocess
import sys
import os

# Check Python version and set appropriate flags
PY2 = sys.version_info[0] == 2
if PY2:
    print("Detected Python 2 - adjusting package installation")

def print_info():
    """Print system information for debugging"""
    try:
        import platform
        print("Python version: %s" % platform.python_version())
        print("Python implementation: %s" % platform.python_implementation())
        print("Platform: %s" % platform.platform())
        print("Architecture: %s" % platform.machine())
        print("System: %s" % platform.system())
    except ImportError:
        print("Python version: %s.%s.%s" % (sys.version_info[0], sys.version_info[1], sys.version_info[2]))
        print("Platform information not available")

def install_packages():
    """Install packages in the correct order with appropriate flags"""
    print("Installing base packages...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--upgrade", 
            "pip", "setuptools", "wheel"
        ])
    except Exception as e:
        print("Warning: Error upgrading base packages: %s" % e)
    
    print("Installing legacy compatibility packages...")
    try:
        # Install packages that work with both Python 2 and 3
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "six", "future"
        ])
    except Exception as e:
        print("Warning: Error installing compatibility packages: %s" % e)
    
    # Select appropriate scientific package versions based on Python version
    if PY2:
        scientific_packages = [
            "numpy==1.16.6",        # Last version compatible with Python 2.7
            "scipy==1.2.3",         # Last version compatible with Python 2.7
            "pandas==0.24.2",       # Last version compatible with Python 2.7
            "scikit-learn==0.20.4", # Last version compatible with Python 2.7
            "joblib==0.14.1"        # Last version compatible with Python 2.7
        ]
    else:
        scientific_packages = [
            "numpy==1.24.4", 
            "scipy==1.10.1", 
            "pandas==2.0.3",
            "scikit-learn==1.1.3",
            "joblib==1.3.2"
        ]
    
    print("Installing scientific packages for Python %s..." % ("2.7" if PY2 else "3.x"))
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--prefer-binary"
        ] + scientific_packages)
    except Exception as e:
        print("Warning: Error installing scientific packages: %s" % e)
        print("Attempting to install packages individually...")
        
        for package in scientific_packages:
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", "--prefer-binary", package
                ])
                print("Successfully installed %s" % package)
            except Exception as pkg_e:
                print("Failed to install %s: %s" % (package, pkg_e))
    
    print("Installing remaining packages from requirements.txt...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--prefer-binary",
            "-r", "requirements.txt"
        ])
    except Exception as e:
        print("Warning: Error installing from requirements.txt: %s" % e)
        # Try installing core packages individually
        essential_packages = ["flask", "flask-cors", "dropbox", "nltk", "gunicorn"]
        for package in essential_packages:
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", package
                ])
                print("Successfully installed %s" % package)
            except Exception:
                print("Failed to install %s" % package)

def verify_packages():
    """Verify that key packages were installed correctly"""
    packages_to_check = [
        "numpy", "scipy", "pandas", "sklearn", "nltk", 
        "flask", "dropbox", "gunicorn"
    ]
    
    print("\nVerifying installed packages:")
    for package in packages_to_check:
        try:
            module = __import__(package)
            version = getattr(module, "__version__", "unknown")
            print("[OK] %s version: %s" % (package, version))
        except ImportError:
            print("[FAIL] Failed to import %s" % package)

if __name__ == "__main__":
    print_info()
    install_packages()
    try:
        verify_packages()
    except Exception as e:
        print("Error during verification: %s" % e)
    print("\nPackage installation completed.")
