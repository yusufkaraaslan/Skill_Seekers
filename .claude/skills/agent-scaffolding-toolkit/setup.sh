#!/bin/bash
# Agent Scaffolding Toolkit Setup Script
# Sets up virtual environment and installs dependencies

set -e

echo "🚀 Agent Scaffolding Toolkit Setup"
echo "=================================="

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found. Please install Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Python $PYTHON_VERSION found"

# Check if version is sufficient
REQUIRED_VERSION="3.10"
if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Error: Python $REQUIRED_VERSION or higher required, found $PYTHON_VERSION"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
if [ -f "pyproject.toml" ]; then
    # Use uv if available, otherwise pip with pyproject.toml
    if command -v uv &> /dev/null; then
        echo "🚀 Using uv for fast installation..."
        uv pip install -e .
    else
        echo "📦 Using pip with pyproject.toml..."
        pip install -e .
    fi
else
    # Fallback to requirements.txt
    pip install -r requirements.txt
fi

# Install development dependencies if requested
if [ "$1" = "--dev" ]; then
    echo "🛠️  Installing development dependencies..."
    pip install -e ".[dev]"
fi

# Verify installation
echo "🔍 Verifying installation..."
python -c "import yaml; print('✅ PyYAML installed successfully')"

# Test basic functionality
echo "🧪 Testing basic functionality..."
python scripts/list_templates.py > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Scripts are working correctly"
else
    echo "⚠️  Warning: Scripts may have issues (check dependencies)"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Usage:"
echo "  source .venv/bin/activate  # Activate virtual environment"
echo "  python scripts/list_templates.py  # List available templates"
echo "  python scripts/create_agent.py  # Create new agent (interactive)"
echo "  python scripts/validate_agent.py --file <agent.md>  # Validate agent"
echo ""
echo "Development mode:"
echo "  ./setup.sh --dev  # Install with development dependencies"
echo "  pytest  # Run tests"
echo "  black scripts/  # Format code"
echo "  mypy scripts/  # Type checking"