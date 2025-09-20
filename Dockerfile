# Use Python 3.9 slim image
FROM python:3.9-slim

# Install system dependencies (ffmpeg for moviepy/whisper, espeak for pyttsx3)
RUN apt-get update && apt-get install -y ffmpeg espeak git && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirement file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ✅ Download spaCy English model during build
RUN python -m spacy download en_core_web_sm

# Copy your app code
COPY . .

# Expose Streamlit default port
EXPOSE 8080

# Run the app with Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
