FROM python:3.12-slim

# Environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Workdir
WORKDIR /ecommerce

# Install system dependencies (needed if we use psycopg2 for PostgreSQL RDS)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Copy and configure the entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose port (Daphne/ASGI)
EXPOSE 8000

# Set the entrypoint to run migrations at container startup
ENTRYPOINT ["/entrypoint.sh"]

# Start Daphne (Passed as arguments to the entrypoint script)
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "ecommerce.asgi:application"]