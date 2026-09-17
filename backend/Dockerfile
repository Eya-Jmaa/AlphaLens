# syntax=docker/dockerfile:1
# Backend Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (gcc for source builds; curl for the healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install. The BuildKit cache mount keeps pip's download
# cache across builds (these deps - torch/transformers/etc. - are large), so
# only the *first* build pays the full download cost.
#
# sentence-transformers pulls in torch with no CUDA available in this container,
# but PyPI's default Linux torch wheel bundles the full CUDA/nvidia toolchain
# anyway (~2GB of unused downloads). Install the CPU-only build first so pip's
# resolver finds torch already satisfied and never reaches for the GPU wheel.
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 alphalens && chown -R alphalens:alphalens /app
USER alphalens

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application (no --reload: that's a dev-only flag)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
