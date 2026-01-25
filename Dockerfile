# Medical Chatbot - Flask RAG app
FROM python:3.10-slim

WORKDIR /app

# Install system deps (for building sentence-transformers / torch-related packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first (better layer caching)
COPY requirements.txt setup.py ./
COPY src ./src

# Install Python dependencies (-e . installs the package)
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code and static assets
COPY app.py ./
COPY templates ./templates
COPY static ./static

# Create data dir for SQLite (chatbot.db); mount volume at runtime for persistence
RUN mkdir -p /app/data

ENV FLASK_APP=app.py
EXPOSE 5000

# Pass PINECONE_API_KEY, AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT via env at runtime
CMD ["python", "app.py"]
