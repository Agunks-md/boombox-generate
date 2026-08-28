FROM python:3.10-slim

# Install system dependencies and FFmpeg
RUN apt-get update && apt-get install -y curl ffmpeg

# Install Node.js v18
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
RUN apt-get install -y nodejs

WORKDIR /app

# Copy all project files
COPY . .

# Install backend dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

# Install frontend dependencies
RUN cd frontend && npm install

# Give execute permission to start script
RUN chmod +x start.sh

# Expose Hugging Face required port
EXPOSE 7860

CMD ["./start.sh"]
