# Updated Dockerfile
FROM python:3.9-slim

# Install system dependencies for Azure Speech SDK
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    ca-certificates \
    libasound2 \
    portaudio19-dev \
    python3-pyaudio \
    ffmpeg \
    alsa-utils \
    libasound2-plugins \
    libsndfile1 \
    curl \
    # Additional dependencies for headless audio
    libpulse0 \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libgbm1 \
    # GStreamer dependencies
    libgstreamer1.0-0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    libgstreamer-plugins-base1.0-dev \
    # ICU libraries for text processing
    libicu-dev \
    # Cleanup
    && rm -rf /var/lib/apt/lists/* \
    && update-ca-certificates

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application
COPY . .

# Create and set permissions for audio directory
RUN mkdir -p /tmp/tts_audio && chmod 777 /tmp/tts_audio

# Set environment variables
ENV PORT=8000
ENV TTS_DEVICE=cpu
ENV CONTAINER_ENV=true
# Azure Speech SDK containerized environment variables
ENV SPEECH_SYNTHESIS_PLATFORM_CONFIG=container
ENV AZURE_SPEECH_CONTAINER=1

EXPOSE 8000

CMD ["python", "-m", "app.main"]