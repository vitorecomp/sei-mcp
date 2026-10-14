# Stage 1: Base Python runtime with dependencies
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies required for lxml
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2 \
    libxslt1.1 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code and bundled WSDL documentation
COPY pyproject.toml ./
COPY sei-documentation ./sei-documentation
COPY src ./src

# Environment defaults for Cloud Run & Load Balancer
ENV PORT=3000 \
    HOST=0.0.0.0 \
    ENV=production \
    SEI_WSDL_PATH=/app/sei-documentation/sei.wsdl

EXPOSE 3000

CMD ["python", "-m", "src.server"]
