#!/bin/bash
# Build script to ensure Python 3.12 is used

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Current Python version: $python_version"

# If Python 3.13, try to use Python 3.12
if [[ "$python_version" == 3.13* ]]; then
    echo "Python 3.13 detected. Attempting to use Python 3.12..."
    # Try to find Python 3.12
    if command -v python3.12 &> /dev/null; then
        python3.12 -m pip install -r requirements.txt
    else
        echo "Python 3.12 not found. Installing audioop-lts for Python 3.13..."
        pip install -r requirements.txt
    fi
else
    pip install -r requirements.txt
fi


