# Open-AutoGLM Docker Image
# Security-hardened fork with RU/EN localization

FROM python:3.11-slim

LABEL maintainer="DmitrL-dev"
LABEL description="AI-powered Android automation agent"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    android-tools-adb \
    libxml2 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -s /bin/bash agent
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies for API
RUN pip install --no-cache-dir \
    fastapi>=0.104.0 \
    uvicorn>=0.24.0 \
    pydantic>=2.5.0

# Copy application code
COPY . .

# Install package
RUN pip install --no-cache-dir -e .

# Change ownership
RUN chown -R agent:agent /app

# Switch to non-root user
USER agent

# Environment variables
ENV PHONE_AGENT_LANG=en
ENV PHONE_AGENT_BASE_URL=http://host.docker.internal:8000/v1

# Expose API port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/')" || exit 1

# Default command: run API server
CMD ["python", "-m", "phone_agent.api", "--host", "0.0.0.0", "--port", "8080"]

# Alternative: run CLI
# CMD ["python", "main.py", "--lang", "en"]
