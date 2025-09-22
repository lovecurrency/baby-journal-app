#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories for the application
mkdir -p data
mkdir -p uploads
mkdir -p static/css
mkdir -p static/js

echo "Build complete!"