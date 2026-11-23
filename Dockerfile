FROM python:3.11-slim

# Create non-root user for hardened container security
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and web assets
COPY backend/ ./backend/
COPY web/ ./web/

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

USER appuser
WORKDIR /app/backend

EXPOSE 8000

CMD ["python", "main.py"]
