
# Use official Python image
FROM python:3.10-slim

# Prevents Python from writing .pyc files
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose Streamlit default port
EXPOSE 8080

# Set environment variable for Streamlit
ENV PORT 8080

# Run Streamlit when container starts
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
