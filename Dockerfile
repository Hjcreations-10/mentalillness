# Use official Python slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (needed for moviepy: ffmpeg + ImageMagick)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
 && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download spacy model
RUN python -m spacy download en_core_web_sm

# Copy your app code into container
COPY . .

# Expose port for Streamlit
EXPOSE 8080

# Run Streamlit on Cloud Run
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
