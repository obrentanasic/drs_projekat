FROM python:3.11-slim

# Set metadata
LABEL maintainer="Quiz Platform Team"
LABEL version="1.0.0"
LABEL description="Distribuirani računarski sistemi 2025/2026 - Quiz Platform Backend"

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    postgresql-client \
    curl \
    redis-tools \
    netcat-openbsd \
    wget \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first (better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p \
    uploads \
    uploads/profile_pictures \
    uploads/quiz_images \
    logs \
    static \
    temp \
    && chmod -R 755 uploads logs

# Create non-root user for security
RUN useradd -m -u 1001 -s /bin/bash quizuser && \
    chown -R quizuser:quizuser /app

# Switch to non-root user
USER quizuser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Default command
CMD ["python", "app.py"]