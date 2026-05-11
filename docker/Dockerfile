# Base image with CUDA support for GPU inference
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# Set environment variables FIRST
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app:/app/src
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3-pip \
    python3.10-venv \
    libgl1-mesa-glx \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt/archives/*

# Set working directory
WORKDIR /app

# Create virtual environment
RUN python3.10 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with verbose output to catch issues
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir fastapi uvicorn pydantic python-multipart PyJWT prometheus-client && \
    pip install --no-cache-dir celery redis psycopg2-binary python-dotenv requests && \
    pip install --no-cache-dir opencv-python numpy pandas pillow scikit-image && \
    pip install --no-cache-dir -r requirements.txt 2>&1 | head -100

# Copy application code BEFORE changing user
COPY src/ ./src/
COPY pipeline/ ./pipeline/

# Create necessary directories
RUN mkdir -p /app/configs /app/data /app/logs

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command (API server)
CMD ["python3.10", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
