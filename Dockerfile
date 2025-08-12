# Use Python 3.11 slim image
FROM python:3.11-slim

# Install system dependencies for MS SQL Server and Ansible
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    unixodbc-dev \
    ansible \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install pyyaml for reading secrets.yml
RUN pip install pyyaml

# Copy Ansible Vault related files
COPY vault_password.txt .
COPY secrets.yml .

# Decrypt secrets.yml using Ansible Vault during image build
RUN ansible-vault decrypt secrets.yml --vault-password-file vault_password.txt

# Copy application files
COPY config/ ./config/
COPY database/ ./database/
COPY ml_sentiment_api/app_with_db.py ./app.py
COPY ml_sentiment_api/sentiment_model.pkl .
COPY ml_sentiment_api/tfidf_vectorizer.pkl .

# Copy test files
COPY test_model.py .
COPY test_api.py .

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Run the application
CMD ["python", "app.py"]


