FROM python:3.11-slim

# System dependencies (PyMuPDF needs libmupdf, ReportLab needs freetype)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    libmupdf-dev \
    mupdf \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create runtime directories
RUN mkdir -p /app/uploads /app/generated_docs

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
