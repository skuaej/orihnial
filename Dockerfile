

FROM python:3.8-slim-bullseye

ENV PIP_NO_CACHE_DIR=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip & setuptools
RUN pip install --upgrade pip setuptools

# Copy app
COPY . /app/
WORKDIR /app/

# Install Python deps
RUN pip install -r requirements.txt

# Run bot
CMD ["python3", "-m", "TEAMZYRO"]
