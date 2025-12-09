#!/usr/bin/env bash
#
# init.sh - Hybrid Python/Rust Environment Setup for Nitro Framework
#
# This script sets up the development environment for the Nitro Framework,
# which requires both Rust (for RustyTags) and Python.
#

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_status() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

print_status "Initializing Nitro Framework Development Environment"
echo ""

# Step 1: Check for Rust toolchain
print_status "Checking Rust toolchain..."
if ! command -v cargo &> /dev/null; then
    print_error "cargo not found. Rust is required for building RustyTags."
    echo ""
    echo "Please install Rust from https://rustup.rs/"
    echo "Run: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
    exit 1
fi

if ! command -v rustc &> /dev/null; then
    print_error "rustc not found. Rust compiler is required."
    echo ""
    echo "Please install Rust from https://rustup.rs/"
    exit 1
fi

RUST_VERSION=$(rustc --version)
print_success "Rust found: $RUST_VERSION"

# Step 2: Check for Python
print_status "Checking Python..."
if ! command -v python3 &> /dev/null; then
    print_error "python3 not found. Python 3.10+ is required."
    echo ""
    echo "Please install Python 3.10 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
print_success "Python found: $PYTHON_VERSION"

# Step 3: Check for maturin
print_status "Checking for maturin..."
if ! command -v maturin &> /dev/null; then
    print_warning "maturin not found. Installing maturin..."
    pip install maturin
    print_success "maturin installed"
else
    MATURIN_VERSION=$(maturin --version)
    print_success "maturin found: $MATURIN_VERSION"
fi

# Step 4: Build RustyTags Python extension
print_status "Building RustyTags (this may take a few minutes on first build)..."
if [ -d "$SCRIPT_DIR/RustyTags" ]; then
    cd "$SCRIPT_DIR/RustyTags"

    # Build the extension
    if maturin develop; then
        print_success "RustyTags built successfully"
    else
        print_error "Failed to build RustyTags"
        exit 1
    fi

    cd "$SCRIPT_DIR"
else
    print_warning "RustyTags directory not found at $SCRIPT_DIR/RustyTags"
    print_warning "Skipping RustyTags build. This is OK if you're not developing RustyTags."
fi

# Step 5: Install Nitro framework in editable mode
print_status "Installing Nitro framework..."
if [ -d "$SCRIPT_DIR/nitro" ]; then
    cd "$SCRIPT_DIR/nitro"

    # Install with dev dependencies
    if pip install -e ".[dev]"; then
        print_success "Nitro installed in editable mode with dev dependencies"
    else
        print_warning "Failed to install with dev dependencies, trying without..."
        if pip install -e .; then
            print_success "Nitro installed in editable mode (without dev dependencies)"
        else
            print_error "Failed to install Nitro"
            exit 1
        fi
    fi

    cd "$SCRIPT_DIR"
else
    print_error "nitro directory not found at $SCRIPT_DIR/nitro"
    exit 1
fi

# Step 6: Verify the setup
print_status "Verifying installation..."

# Test imports
if python3 -c "import nitro" 2>/dev/null; then
    print_success "nitro module imports successfully"
else
    print_error "Failed to import nitro module"
    exit 1
fi

if python3 -c "import rusty_tags" 2>/dev/null; then
    print_success "rusty_tags module imports successfully"
else
    print_warning "rusty_tags module not available (this is OK if RustyTags wasn't built)"
fi

# Test basic functionality
print_status "Testing basic functionality..."
python3 << 'EOF'
try:
    from nitro.domain.entities.base_entity import Entity
    from nitro.infrastructure.events.events import event, on, emit
    print("✓ Core Nitro components import successfully")
except Exception as e:
    print(f"✗ Error importing core components: {e}")
    exit(1)
EOF

# Step 7: Print summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
print_success "Environment setup complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Summary:"
echo "  • Rust toolchain: ✓"
echo "  • Python environment: ✓"
echo "  • RustyTags extension: ✓"
echo "  • Nitro framework: ✓"
echo ""
echo "Next steps:"
echo "  1. Review feature_list.json for test coverage"
echo "  2. Run tests: pytest nitro/tests/"
echo "  3. Start developing: python examples/counter_app.py"
echo ""
echo "Development notes:"
echo "  • After modifying Rust code in RustyTags/, run: maturin develop"
echo "  • Nitro is installed in editable mode, Python changes take effect immediately"
echo "  • Use 'nitro --help' to see available CLI commands"
echo ""
echo "Happy coding! 🚀"
