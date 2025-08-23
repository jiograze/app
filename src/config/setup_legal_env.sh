#!/bin/bash

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install core requirements
echo "Installing core requirements..."
pip install -r requirements-legal.txt

# Install Turkish language model
echo "Installing Turkish language model..."
python -m spacy download tr_core_news_md

# Install transformers for advanced NLP
echo "Installing transformers..."
pip install transformers

# Install additional legal NLP libraries
echo "Installing legal NLP libraries..."
pip install legal-nlp

# Install visualization tools
echo "Installing visualization tools..."
pip install matplotlib seaborn

echo "Setup completed successfully!"
echo "Activate the virtual environment with: source .venv/bin/activate"
