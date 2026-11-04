# Production Dockerfile for ASHA Mobile EHR Companion
FROM python:3.13-slim

WORKDIR /app

# Prevent Python from writing .pyc and buffer stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and database
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY start_system.py .
COPY asha_pregnancy_tracker.db .

EXPOSE 8000

# Start server
CMD ["python", "start_system.py"]

