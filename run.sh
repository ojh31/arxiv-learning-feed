#!/bin/bash

# Change to the directory of the script
cd "$(dirname "${BASH_SOURCE[0]}")"

# Activate the virtual environment
source venv/bin/activate

# Create a timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Run the Python script and save output with timestamp
mkdir -p output
python main.py > "output/output_${TIMESTAMP}.txt"