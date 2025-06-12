# S3 FastMCP Server
A Model Context Protocol (MCP) server for interacting with S3-compatible storage services like AWS S3/MinIO.

## Overview
This project implements a FastMCP server that exposes S3 storage operations through a simple API. It allows clients to perform common S3 operations such as listing buckets, creating/deleting buckets, uploading/downloading objects, and more.

## Features
 - **S3 Operations**: List, create, and delete buckets
 - **Object Management**: List, upload, download, and delete objects
 - **MinIO Support**: Works with both AWS S3 and MinIO
 - **Interactive Client**: Command-line client for testing and interacting with the server
 - **Kubernetes Deployment**: Deploy on Kubernetes with the provided manifests
 - **Docker Integration**: Works with MinIO running as a Docker container

## Prerequisites
 - Python 3.13 or newer
 - An S3-compatible storage service (AWS S3 or MinIO)
 - S3 credentials (Access Key and Secret Key)
 - Docker Desktop with Kubernetes enabled (for Kubernetes deployment)
 - `kubectl` CLI tool

## Installation
 1. Clone the repository:
 ```bash
 git clone https://github.com/rajesh1084/sample-fastmcp-server-s3.git
 cd sample-fastmcp-server-s3
 ```

 2. Create and activate a virtual environment:
 ```bash
 python -m venv .venv
 source .venv/bin/activate
 ```
 3. Install dependencies:
 ```bash
 pip install -e .
 ```

## Configuration
Create a `.env` file in the project root with your S3 configuration:
```bash
# AWS Configuration (Only for standalone server, not required for k8s deployment)
S3_ENDPOINT_URL=http://localhost:9000  # For MinIO
AWS_REGION=ind-south-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```
## Deployment Options
Option 1: Running Locally
**Note**: Please check and update the MinIO API port.

Start the FastMCP server:
```bash
cd src/s3_fast_mcp_server
python remote_fastmcp_server.py
```

The server will start on http://localhost:9999 by default.

Option 2: Deploying to Kubernetes
**Note**:
 - Kubernetes is a pre-requisite
 - Please check and update the MinIO API port in `k8s/configmap.yaml`
```bash
./automation.sh
```
The FastMCP server will be accessible at http://localhost:30999/sse
Use this URL in the `sse_client.py` (`SERVER_URL`)

## Running the Client
The package includes an interactive client to test the S3 operations:
```bash
cd src
python sse_client.py
```

## Notes
 - MinIO compatibility is enabled with appropriate configuration
 - SSL verification is disabled for MinIO by default

## License
