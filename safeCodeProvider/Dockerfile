# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install supervisord
RUN apt-get update && apt-get install -y supervisor

# Copy the rest of the application code into the container
COPY . .

# Copy the supervisord configuration file
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose the ports for the student and teacher servers
EXPOSE 8000 8001

# Start supervisord
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]