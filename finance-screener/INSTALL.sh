#!/bin/bash
# Quick installation and test script for finance-screener
# Run: bash INSTALL.sh

set -e  # Exit on error

echo "========================================="
echo "Finance Screener - TDD Installation"
echo "========================================="
echo ""

# Check Python version
echo "✓ Checking Python version..."
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ Python 3 not found. Please install Python 3.10+"
    exit 1
fi

# Create virtual environment
echo ""
echo "✓ Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "✓ Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "✓ Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
echo ""
echo "✓ Installing dependencies (this may take 2-3 minutes)..."
pip install -e ".[dev]" --quiet

# Copy environment template
echo ""
echo "✓ Creating .env file from template..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠️  Please edit .env with your API keys:"
    echo "   - ANTHROPIC_API_KEY"
    echo "   - GOOGLE_API_KEY"
    echo "   - SEC_USER_AGENT (must include your email)"
else
    echo "✅ .env already exists (not overwriting)"
fi

# Run verification script
echo ""
echo "✓ Running setup verification..."
python3 verify_setup.py

# Check if verification passed
if [ $? -eq 0 ]; then
    echo ""
    echo "========================================="
    echo "✅ Installation Complete!"
    echo "========================================="
    echo ""
    echo "Next steps:"
    echo "  1. Edit .env with your API keys"
    echo "  2. Run tests: pytest -v"
    echo "  3. Check coverage: pytest --cov"
    echo ""
    echo "Quick test commands:"
    echo "  - Unit tests only:    pytest -m unit"
    echo "  - Skip slow tests:    pytest -m 'not slow'"
    echo "  - Discovery tests:    pytest tests/test_discovery.py -v"
    echo "  - Ingestion tests:    pytest tests/test_ingestion.py -v"
    echo ""
else
    echo ""
    echo "⚠️  Setup verification had some warnings."
    echo "This is expected if dependencies aren't installed yet."
    echo ""
    echo "Try running tests anyway:"
    echo "  pytest -v"
fi
