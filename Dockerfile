FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create volume mount points for persistent data
VOLUME /app/database

# Expose port
EXPOSE 8000

# Start application with proper host binding
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]