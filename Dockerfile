# --- Stage 1: Build dependencies ---
    FROM python:3.11-slim AS builder

    WORKDIR /app
    
    # Install build dependencies
    RUN apt-get update && apt-get install -y \
        gcc \
        libpq-dev \
        git && \
        rm -rf /var/lib/apt/lists/*
    
    # Install Python packages
    COPY requirements.txt .
    RUN pip install --upgrade pip && \
        pip install --no-cache-dir --prefix=/install -r requirements.txt
    
    # --- Stage 2: Final image ---
    FROM python:3.11-slim
    
    WORKDIR /app
    
    # Install runtime dependencies only

     RUN apt-get update && apt-get install -y \
     libpq-dev \
     ffmpeg \
     && rm -rf /var/lib/apt/lists/*
    
    # Copy installed packages from builder
    COPY --from=builder /install /usr/local
    
    # Copy application code
    COPY . /app/
    
    EXPOSE 8001

    CMD ["sh", "-c", "echo 'Container ready. Use docker-compose commands to start services.'"]
    #CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "main.wsgi:application"]
    