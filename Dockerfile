FROM python:3.12-slim

# Environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Workdir
WORKDIR /ecommerce

# Install deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy project
COPY . .

#Expose port (gunicorn)
EXPOSE 8000

#Start Gunicorn
CMD ["daphne","-b","0.0.0.0","-p","8000","ecommerce.asgi:application"]