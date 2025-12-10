# Nitro Framework - Production Dockerfile
#
# This Dockerfile demonstrates containerization of a Nitro-based application
# with best practices for Python web applications.

FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Create non-root user for security
RUN useradd -m -u 1000 nitro && \
    chown -R nitro:nitro /app

USER nitro

# Expose default port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=2)" || exit 1

# Default command - run a Nitro example app
# Override this in production with your actual app
CMD ["uvicorn", "examples.starlette_counter_app:app", "--host", "0.0.0.0", "--port", "8000"]
