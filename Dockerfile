# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Update system packages and install dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       libxml2-dev \
       libxslt-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container to /app
WORKDIR /app

# Copy the requirements file to the container
COPY requirements.txt /app/

# Install Python dependencies listed in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the static directory separately for debugging
COPY static /app/static

# Debugging: Create a marker file to verify the presence of the static directory
RUN touch /app/static/marker_file_static.txt

# Debugging: List contents of /app directory
RUN echo "Contents of /app directory:" && ls -la /app

# Debugging: List contents of /app/static directory
RUN echo "Contents of /app/static directory:" && ls -la /app/static

# Copy the rest of the application's code to the container
COPY . /app

# Debugging: Create a marker file to verify the presence of all files
RUN touch /app/marker_file_all.txt

# Debugging: List contents of /app directory again
RUN echo "Contents of /app directory after copying all files:" && ls -la /app

# Ensure required directories exist
RUN mkdir -p /app/logs /app/config /app/static /app/temp /app/templates

# Expose port 5001 to allow communication to/from the server
EXPOSE 5001

# Use Gunicorn to serve the application
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5001", "webhook_listener:app"]
