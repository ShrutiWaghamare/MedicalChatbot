# Medical Chatbot - Flask RAG app
FROM python:3.10-slim

WORKDIR /app

# Set environment to use CPU-only torch (no CUDA) to save space
ENV TORCH_CUDA_ARCH_LIST=""
ENV BUILD_WITH_CUDA="0"

# Install system deps (for building sentence-transformers / torch-related packages)
# Clean up immediately after each step to save space
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

# Upgrade pip first and clean cache
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip cache purge || true

# Copy dependency files first (better layer caching)
COPY requirements.txt setup.py ./
COPY src ./src

# Install Python dependencies with CPU-only torch
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt \
    && pip cache purge || true \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/* \
    && rm -rf /root/.cache

# Remove build dependencies to reduce final image size
RUN apt-get remove -y gcc g++ build-essential \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/* \
    && rm -rf /root/.cache

# Copy app code and static assets
COPY app.py ./
COPY templates ./templates
COPY static ./static

# Create data dir for SQLite (chatbot.db); mount volume at runtime for persistence
RUN mkdir -p /app/data

ENV FLASK_APP=app.py
ENV FLASK_ENV=production
EXPOSE 5000

# Pass PINECONE_API_KEY, AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT via env at runtime
CMD ["python", "app.py"]
