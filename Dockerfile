# Use Python 3.13 as base image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml README.md ./
COPY src ./src

# Install dependencies
RUN pip install --no-cache-dir -e .

# Create a directory for the .env file
RUN mkdir -p /app/config

# Expose the port used by the server
EXPOSE 9999

# Command to run the server
CMD ["python", "src/s3_fast_mcp_server/remote_fastmcp_server.py"]