# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# Create directory for knowledge base if needed
RUN mkdir -p /app/knowledge_base

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Expose the port that Cloud Run expects
EXPOSE 8080

# Run the bot
CMD ["python", "src/bot.py"]
