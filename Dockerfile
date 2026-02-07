# Skill Seekers - Multi-stage Docker Build
# Optimized for production deployment with minimal image size

# Stage 1: Builder - Install dependencies and build
FROM python:3.12-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml README.md ./
COPY src/ src/

# Install dependencies and build package
RUN pip install --no-cache-dir --upgrade pip uv && \
    uv pip install --system --no-cache -e . && \
    uv pip install --system --no-cache ".[all-llms]"

# Stage 2: Runtime - Minimal production image
FROM python:3.12-slim

LABEL maintainer="Skill Seekers <noreply@skillseekers.dev>"
LABEL description="Skill Seekers - Convert documentation to AI skills"
LABEL version="2.9.0"

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash skillseeker && \
    mkdir -p /app /data /configs /output && \
    chown -R skillseeker:skillseeker /app /data /configs /output

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/skill-seekers* /usr/local/bin/

# Copy application code
COPY --chown=skillseeker:skillseeker src/ src/
COPY --chown=skillseeker:skillseeker configs/ configs/
COPY --chown=skillseeker:skillseeker pyproject.toml README.md ./

# Switch to non-root user
USER skillseeker

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/skillseeker/.local/bin:$PATH" \
    SKILL_SEEKERS_HOME=/data \
    SKILL_SEEKERS_OUTPUT=/output

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD skill-seekers --version || exit 1

# Default volumes
VOLUME ["/data", "/configs", "/output"]

# Expose MCP server port (HTTP mode)
EXPOSE 8765

# Default command - show help
CMD ["skill-seekers", "--help"]
