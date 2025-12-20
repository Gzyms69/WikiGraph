#!/bin/bash
# ~/WikiGraph/setup_environment.sh

echo "Setting up Polish Wikipedia Knowledge Graph environment..."
echo "======================================================"

# Create directory structure
mkdir -p ~/WikiGraph/{scripts,raw_data,processed_batches,databases,logs,app/{templates,static}}

echo "Directory structure created."

# Install Python dependencies (basic set for prototype)
echo "Installing Python dependencies..."
pip3 install mwxml mwparserfromhell tqdm

echo "Basic dependencies installed."
echo ""
echo "To test the prototype parser, run:"
echo "  python3 ~/WikiGraph/scripts/phase1_parser_v1.py"
echo ""
echo "Then verify with:"
echo "  python3 ~/WikiGraph/scripts/verify_prototype.py"
echo ""
echo "For full environment setup, install additional packages:"
echo "  pip3 install -r ~/WikiGraph/requirements.txt"
