#!/bin/bash

# init.sh - Setup and launch the Nitro Documentation Platform
# This script handles environment setup, dependency installation, and application startup

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                           ║${NC}"
echo -e "${BLUE}║        Nitro Documentation Platform - Initializer         ║${NC}"
echo -e "${BLUE}║                                                           ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if we're in the right directory
if [ ! -d "nitro" ]; then
    echo -e "${RED}Error: nitro/ directory not found. Please run this script from the project root.${NC}"
    exit 1
fi

# Step 1: Install Nitro framework in editable mode
echo -e "${YELLOW}[1/5] Installing Nitro framework in editable mode...${NC}"
cd nitro
if pip install -e ".[dev]" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Nitro framework installed successfully${NC}"
else
    echo -e "${RED}✗ Failed to install Nitro framework${NC}"
    exit 1
fi
cd ..

# Step 2: Verify imports
echo -e "${YELLOW}[2/5] Verifying package imports...${NC}"

# Check nitro import
if python -c "import nitro" 2>/dev/null; then
    echo -e "${GREEN}✓ nitro package imports successfully${NC}"
else
    echo -e "${RED}✗ Failed to import nitro package${NC}"
    exit 1
fi

# Check rusty_tags import
if python -c "import rusty_tags" 2>/dev/null; then
    echo -e "${GREEN}✓ rusty_tags package imports successfully${NC}"
else
    echo -e "${RED}✗ Failed to import rusty_tags package${NC}"
    exit 1
fi

# Check mistletoe import (or install if missing)
if ! python -c "import mistletoe" 2>/dev/null; then
    echo -e "${YELLOW}  Installing mistletoe...${NC}"
    pip install mistletoe > /dev/null 2>&1
fi

if python -c "import mistletoe" 2>/dev/null; then
    echo -e "${GREEN}✓ mistletoe package imports successfully${NC}"
else
    echo -e "${RED}✗ Failed to import mistletoe package${NC}"
    exit 1
fi

# Step 3: Set up PYTHONPATH if needed
echo -e "${YELLOW}[3/5] Configuring Python path...${NC}"
export PYTHONPATH="${PWD}:${PWD}/nitro:${PYTHONPATH}"
echo -e "${GREEN}✓ PYTHONPATH configured${NC}"

# Step 4: Initialize docs_app directory structure
echo -e "${YELLOW}[4/5] Verifying docs_app directory structure...${NC}"
DOCS_APP_DIR="nitro/docs_app"

# Create necessary directories if they don't exist
mkdir -p "${DOCS_APP_DIR}"/{domain,infrastructure/{markdown,navigation},components,pages,content}

# Create __init__.py files
touch "${DOCS_APP_DIR}/__init__.py"
touch "${DOCS_APP_DIR}/domain/__init__.py"
touch "${DOCS_APP_DIR}/infrastructure/__init__.py"
touch "${DOCS_APP_DIR}/infrastructure/markdown/__init__.py"
touch "${DOCS_APP_DIR}/components/__init__.py"
touch "${DOCS_APP_DIR}/pages/__init__.py"

echo -e "${GREEN}✓ Directory structure verified/created${NC}"

# Step 5: Start the FastAPI application
echo -e "${YELLOW}[5/5] Starting Documentation Platform...${NC}"
echo ""

# Check if app.py exists
if [ ! -f "${DOCS_APP_DIR}/app.py" ]; then
    echo -e "${YELLOW}Warning: ${DOCS_APP_DIR}/app.py not found. Creating placeholder...${NC}"
    cat > "${DOCS_APP_DIR}/app.py" << 'EOF'
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="Nitro Documentation Platform")

@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <html>
        <head>
            <title>Nitro Docs - Coming Soon</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }
                .container {
                    text-align: center;
                }
                h1 {
                    font-size: 3rem;
                    margin-bottom: 1rem;
                }
                p {
                    font-size: 1.2rem;
                    opacity: 0.9;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 Nitro Documentation Platform</h1>
                <p>Foundation is ready. Implementation in progress...</p>
            </div>
        </body>
    </html>
    """

@app.get("/health")
def health():
    return {"status": "ok", "service": "nitro-docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF
fi

# Launch banner
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                           ║${NC}"
echo -e "${GREEN}║      🚀 Nitro Documentation Platform Starting...         ║${NC}"
echo -e "${GREEN}║                                                           ║${NC}"
echo -e "${GREEN}║      Access at: ${BLUE}http://localhost:8000${GREEN}                    ║${NC}"
echo -e "${GREEN}║      API docs:  ${BLUE}http://localhost:8000/docs${GREEN}               ║${NC}"
echo -e "${GREEN}║                                                           ║${NC}"
echo -e "${GREEN}║      Press Ctrl+C to stop the server                     ║${NC}"
echo -e "${GREEN}║                                                           ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Start uvicorn with reload enabled
cd "${DOCS_APP_DIR}"
exec uvicorn app:app --host 0.0.0.0 --port 8000 --reload
