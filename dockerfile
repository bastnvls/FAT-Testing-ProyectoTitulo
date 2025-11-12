# Base image
FROM python:3.10-slim-buster

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose port 5000
EXPOSE 80

# Run the application
#CMD ["bash"]
CMD ["python", "__init__.py"]
