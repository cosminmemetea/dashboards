FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies (including gunicorn and nginx)
RUN apt-get update && apt-get install -y \
    nginx \
    build-essential \
    gcc \
    curl \
    && pip install --upgrade pip \
    && apt-get clean

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt \
    && pip install gunicorn

# Copy source code
COPY . .

# Copy nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Copy and make entrypoint executable
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Clean up default nginx site
RUN rm -f /etc/nginx/sites-enabled/default

EXPOSE 80

# Use JSON-style CMD
CMD ["sh", "-c", "service nginx start && ./start.sh"]
