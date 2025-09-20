# Use official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies for moviepy & other packages
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# ✅ Download SpaCy English model
RUN python -m spacy download en_core_web_sm

# Copy app files
COPY . .

# Run Streamlit on Cloud Run
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]

