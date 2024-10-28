# Use an official Python runtime as the base image
FROM python:3.8.2

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    STREAMLIT_PORT=8501 \
    FLASK_PORT=5000

# Set working directory
WORKDIR /app

# Install system dependencies for video processing
RUN apt-get update && \
    apt-get install -y \
        libgl1-mesa-glx \
        libv4l-dev \
        v4l-utils \
        ffmpeg \
        libsm6 \
        libxext6 && \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the app files into the container
COPY . /app

# Expose ports for Streamlit and Flask
EXPOSE 8501 5000

# CMD will be overridden in docker-compose.yml
CMD ["bash"]

