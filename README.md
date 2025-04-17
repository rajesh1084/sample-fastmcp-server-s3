# S3 FastMCP Server
A Machine Communication Protocol (MCP) server for interacting with S3-compatible storage services like AWS S3 and MinIO.

## Overview
This project implements a FastMCP server that exposes S3 storage operations through a simple API. It allows clients to perform common S3 operations such as listing buckets, creating/deleting buckets, uploading/downloading objects, and more.

## Features
 - **S3 Operations**: List, create, and delete buckets
 - **Object Management**: List, upload, download, and delete objects
 - **MinIO Support**: Works with both AWS S3 and MinIO
 - **Interactive Client**: Command-line client for testing and interacting with the server

## Prerequisites
 - Python 3.13 or newer
 - An S3-compatible storage service (AWS S3 or MinIO)
 - S3 credentials (access key and secret key)

## Installation
 1. Clone the repository:
 ```bash
 git clone https://github.com/yourusername/sample-fastmcp-server-s3.git
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
# AWS Configuration
S3_ENDPOINT_URL=http://localhost:9000  # For MinIO
AWS_REGION=your-region
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

## Running the Server
Start the FastMCP server:
```bash
cd src/s3_fast_mcp_server
python remote_fastmcp_server.py
```

The server will start on http://localhost:9999 by default.

## Running the Client
The package includes an interactive client to test the S3 operations:
```bash
cd src
python sse_client.py
```

## Available Operations
The client provides a menu-driven interface for the following operations:

 1. List Buckets: View all accessible S3 buckets
 2. Create Bucket: Create a new S3 bucket
 3. Delete Bucket: Delete an existing bucket (with option to force delete non-empty buckets)
 4. List Objects: View objects in a specified bucket
 5. Get Object: Retrieve and display the contents of an object
 6. Upload Object: Create a new object with specified content
 7. Delete Object: Remove an object from a bucket

## Example Usage
Creating a Bucket
```bash
Select an operation (1-8): 2
Enter name for new bucket: my-test-bucket
Enter region (leave blank for default): 
```

Uploading an Object
```bash
Select an operation (1-8): 6
Enter bucket name: my-test-bucket
Enter object key for the new file: hello.txt
Enter content for the new file: Hello, S3 world!
```

Retrieving an Object
```bash
Select an operation (1-8): 5
Enter bucket name: my-test-bucket
Enter object key: hello.txt
```

## Notes
 - The server uses a custom S3Resource class to handle S3 operations asynchronously
 - MinIO compatibility is enabled with appropriate configuration
 - SSL verification is disabled for MinIO by default

## License
