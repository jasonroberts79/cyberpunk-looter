# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies and uv
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && rm -rf /var/lib/apt/lists/*

# Add uv to PATH
ENV PATH="/root/.cargo/bin:$PATH"

# Copy dependency files for better layer caching
COPY pyproject.toml uv.lock ./

# Install Python dependencies using uv
RUN uv sync --frozen --no-dev

# Copy application code
COPY src/ ./src/

# Copy knowledge base files
COPY knowledge_base/ ./knowledge_base/

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the bot using uv
CMD ["uv", "run", "src/bot.py"]
