import asyncio
import logging
import os
import base64
from urllib.parse import unquote

import boto3
from botocore.config import Config
from dotenv import load_dotenv

from mcp.server.fastmcp.server import FastMCP
from mcp.server.sse import SseServerTransport
from mcp.types import TextContent, ImageContent, GetPromptResult

# Import the S3Resource class
from resources.s3_resource import S3Resource

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_s3_server")

# Create SSE transport with explicit endpoint configuration
sse_transport = SseServerTransport(endpoint="/sse")

# Create a FastMCP server
server = FastMCP(
    name="S3MCPServer",
    instructions="An MCP server for interacting with S3 storage.",
    host="localhost",
    port=9999,
)

# Initialize S3 resource
max_buckets = int(os.getenv("S3_MAX_BUCKETS", "5"))
s3_resource = S3Resource(
    region_name=os.getenv("AWS_REGION", "us-east-1"),
    max_buckets=max_buckets,
    endpoint_url=os.getenv("S3_ENDPOINT_URL", None),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", None),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", None),
)

# Configure boto3 client for S3/MinIO
minio_config = Config(
    signature_version="s3v4",
    region_name=os.getenv("AWS_REGION", "us-east-1"),
)

boto3_s3_client = boto3.client(
    "s3",
    endpoint_url=os.getenv("S3_ENDPOINT_URL", None),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", None),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", None),
    config=minio_config,
    verify=False,  # Disable SSL verification for MinIO
)


# Define S3 resource handlers using FastMCP decorators
@server.resource(
    "s3://{bucket}/{key}",
    name="S3 Object",
    description="Access S3 objects using s3://bucket/key format",
)
async def get_s3_object(bucket: str, key: str) -> str:
    """Read content from an S3 resource and return it"""
    logger.debug(f"Reading S3 object - Bucket: {bucket}, Key: {key}")

    try:
        response = await s3_resource.get_object(bucket, key)
        content_type = response.get("ContentType", "")
        logger.debug(f"Read MIMETYPE response: {content_type}")

        # Rest of function remains the same, just replace 'path' with 'key'
        if "Body" in response:
            if isinstance(response["Body"], bytes):
                data = response["Body"]
            else:
                # Handle streaming response
                async with response["Body"] as stream:
                    data = await stream.read()

            # Process the data based on file type
            if s3_resource.is_text_file(key):  # Changed from path to key
                # Return plain text for text files
                try:
                    return data.decode("utf-8")
                except UnicodeDecodeError:
                    # Fall back to base64 if not valid UTF-8
                    return base64.b64encode(data).decode("utf-8")
            else:
                # Return base64 encoded data for binary files
                return base64.b64encode(data).decode("utf-8")
        else:
            raise ValueError("No data in response body")

    except Exception as e:
        logger.error(
            f"Error reading object {key} from bucket {bucket}: {str(e)}"
        )  # Changed from path to key
        raise ValueError(f"Error reading S3 object: {str(e)}")


# Tool: List S3 Buckets
@server.tool(
    name="ListBuckets",
    description="List S3 buckets available to the authenticated user",
)
async def list_buckets_tool() -> dict:
    """List all available S3 buckets"""
    try:
        buckets = await s3_resource.list_buckets(None)
        return {"buckets": buckets}
    except Exception as e:
        logger.error(f"Error listing buckets: {str(e)}")
        raise ValueError(f"Failed to list buckets: {str(e)}")


# Tool: Create Bucket
@server.tool(name="CreateBucket", description="Create a new S3 bucket")
async def create_bucket_tool(bucket: str, region: str = "") -> dict:
    """Create a new S3 bucket with the specified name"""
    try:
        # If region not provided or empty, use the default region
        region_name = region or os.getenv("AWS_REGION", "us-east-1")

        # For regions other than us-east-1, we need to specify LocationConstraint
        if region_name != "us-east-1":
            response = boto3_s3_client.create_bucket(
                Bucket=bucket,
                CreateBucketConfiguration={"LocationConstraint": region_name},
            )
        else:
            response = boto3_s3_client.create_bucket(Bucket=bucket)

        logger.info(f"Successfully created bucket: {bucket}")
        return {"status": "success", "bucket": bucket, "response": str(response)}
    except Exception as e:
        logger.error(f"Error creating bucket {bucket}: {str(e)}")
        raise ValueError(f"Failed to create bucket: {str(e)}")


# Tool: Delete Bucket
@server.tool(name="DeleteBucket", description="Delete an empty S3 bucket")
async def delete_bucket_tool(bucket: str, force: bool = False) -> dict:
    """Delete an S3 bucket (bucket must be empty unless force=True)"""
    try:
        if force:
            # Check if bucket exists first
            try:
                boto3_s3_client.head_bucket(Bucket=bucket)
            except:
                return {
                    "status": "success",
                    "message": f"Bucket {bucket} does not exist",
                }

            # List and delete all objects
            paginator = boto3_s3_client.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=bucket):
                if "Contents" in page:
                    objects = [{"Key": obj["Key"]} for obj in page["Contents"]]
                    boto3_s3_client.delete_objects(
                        Bucket=bucket, Delete={"Objects": objects}
                    )

            # Delete any versioned objects if versioning is enabled
            paginator = boto3_s3_client.get_paginator("list_object_versions")
            try:
                for page in paginator.paginate(Bucket=bucket):
                    delete_markers = []
                    if "DeleteMarkers" in page:
                        delete_markers = [
                            {"Key": marker["Key"], "VersionId": marker["VersionId"]}
                            for marker in page["DeleteMarkers"]
                        ]
                    versions = []
                    if "Versions" in page:
                        versions = [
                            {"Key": version["Key"], "VersionId": version["VersionId"]}
                            for version in page["Versions"]
                        ]

                    if delete_markers or versions:
                        boto3_s3_client.delete_objects(
                            Bucket=bucket, Delete={"Objects": delete_markers + versions}
                        )
            except:
                # Versioning might not be enabled
                pass

        # Now delete the bucket
        response = boto3_s3_client.delete_bucket(Bucket=bucket)
        logger.info(f"Successfully deleted bucket: {bucket}")
        return {
            "status": "success",
            "message": f"Bucket {bucket} deleted",
            "response": str(response),
        }
    except Exception as e:
        logger.error(f"Error deleting bucket {bucket}: {str(e)}")
        raise ValueError(f"Failed to delete bucket: {str(e)}")


# Tool: List Objects in a Bucket
@server.tool(
    name="ListObjects",
    description="List objects in an S3 bucket with optional prefix filtering",
)
async def list_objects_tool(
    bucket: str, prefix: str = "", max_keys: int = 1000
) -> dict:
    """List objects in the specified bucket with optional prefix filtering"""
    try:
        objects = await s3_resource.list_objects(
            bucket, prefix=prefix, max_keys=max_keys
        )
        return {"objects": objects}
    except Exception as e:
        logger.error(f"Error listing objects in bucket {bucket}: {str(e)}")
        raise ValueError(f"Failed to list objects: {str(e)}")


# Tool: Get Object
@server.tool(
    name="GetObject", description="Retrieve an object from S3 by bucket and key"
)
async def get_object_tool(bucket: str, key: str) -> str:
    """Get an object from S3 by bucket and key"""
    try:
        response = boto3_s3_client.get_object(Bucket=bucket, Key=key)
        file_content = response["Body"].read().decode("utf-8", errors="replace")
        return file_content
    except Exception as e:
        logger.error(f"Error getting object {key} from bucket {bucket}: {str(e)}")
        raise ValueError(f"Failed to get object: {str(e)}")


# Tool: Put Object
@server.tool(name="PutObject", description="Upload content to an S3 object")
async def put_object_tool(
    bucket: str, key: str, content: str, content_type: str = "text/plain"
) -> dict:
    """Upload content to an S3 object"""
    try:
        response = boto3_s3_client.put_object(
            Bucket=bucket, Key=key, Body=content, ContentType=content_type
        )
        return {"status": "success", "response": str(response)}
    except Exception as e:
        logger.error(f"Error putting object {key} to bucket {bucket}: {str(e)}")
        raise ValueError(f"Failed to put object: {str(e)}")


# Tool: Delete Object
@server.tool(name="DeleteObject", description="Delete an object from S3")
async def delete_object_tool(bucket: str, key: str) -> dict:
    """Delete an object from S3"""
    try:
        response = boto3_s3_client.delete_object(Bucket=bucket, Key=key)
        return {"status": "success", "response": str(response)}
    except Exception as e:
        logger.error(f"Error deleting object {key} from bucket {bucket}: {str(e)}")
        raise ValueError(f"Failed to delete object: {str(e)}")


if __name__ == "__main__":
    # Run the server with the SSE transport
    logger.info("Starting S3 MCP server on http://0.0.0.0:8000")
    server.run(transport="sse")
