import asyncio
import logging
from mcp import ClientSession
from mcp.client.sse import sse_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-s3-client")

SERVER_URL = "http://localhost:30999/sse"  # Change this to your server URL


async def main():
    # Connect to the remote server via SSE
    logger.info(f"Connecting to S3 MCP server at {SERVER_URL}")

    async with sse_client(SERVER_URL) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # Initialize the connection
            await session.initialize()
            logger.info("Connection initialized")

            # List available tools
            try:
                logger.info("Retrieving available tools...")
                # Get list of available tools
                tools = await session.list_tools()

                if tools:
                    print("\nAvailable Tools:")
                    for tool in tools:
                        # Handle different possible formats of tool information
                        if hasattr(tool, "name") and hasattr(tool, "description"):
                            # Object with attributes
                            print(f"- {tool.name}: {tool.description}")
                        elif isinstance(tool, tuple) and len(tool) >= 2:
                            # Tuple with name and description
                            print(f"- {tool[0]}: {tool[1]}")
                        elif isinstance(tool, dict) and "name" in tool:
                            # Dictionary with name key
                            print(f"- {tool['name']}: {tool.get('description', '')}")
                        else:
                            # Just print the tool as is
                            print(f"- {tool}")
                else:
                    print("\nNo tools available from server")
            except Exception as e:
                print(f"Error retrieving tools: {e}")
                # Continue anyway since we know the tools we want to use
                print("\nContinuing with known operations...")

            # Main menu for operations
            while True:
                print("\n=== S3 Operations Menu ===")
                print("1. List Buckets")
                print("2. Create Bucket")
                print("3. Delete Bucket")
                print("4. List Objects in Bucket")
                print("5. Get Object")
                print("6. Upload Object")
                print("7. Delete Object")
                print("8. Exit")

                choice = input("\nSelect an operation (1-8): ")

                if choice == "1":
                    # List available buckets
                    logger.info("Listing buckets...")
                    buckets_result = await session.call_tool("ListBuckets")

                    if isinstance(buckets_result, dict) and "buckets" in buckets_result:
                        buckets = buckets_result["buckets"]
                        print("\nAvailable Buckets:")
                        for bucket in buckets:
                            if isinstance(bucket, dict) and "Name" in bucket:
                                print(f"- {bucket['Name']}")
                    else:
                        print(f"\nBuckets response: {buckets_result}")

                elif choice == "2":
                    # Create a new bucket
                    bucket_name = input("Enter name for new bucket: ")
                    region = input("Enter region (leave blank for default): ")

                    logger.info(f"Creating bucket: {bucket_name}")
                    try:
                        result = await session.call_tool(
                            "CreateBucket",
                            {
                                "bucket": bucket_name,
                                "region": region
                                or "",  # Use empty string instead of None
                            },
                        )
                        print(f"\nBucket creation result: {result}")
                    except Exception as e:
                        print(f"Error creating bucket: {e}")

                elif choice == "3":
                    # Delete a bucket
                    bucket_name = input("Enter bucket name to delete: ")
                    force = (
                        input("Force deletion of non-empty bucket? (y/n): ").lower()
                        == "y"
                    )

                    logger.info(f"Deleting bucket: {bucket_name} (force={force})")
                    try:
                        result = await session.call_tool(
                            "DeleteBucket", {"bucket": bucket_name, "force": force}
                        )
                        print(f"\nBucket deletion result: {result}")
                    except Exception as e:
                        print(f"Error deleting bucket: {e}")

                elif choice == "4":
                    # List objects in bucket
                    bucket_name = input("Enter bucket name to list objects: ")
                    prefix = input("Enter prefix filter (optional): ")

                    logger.info(f"Listing objects in bucket {bucket_name}...")
                    try:
                        objects_result = await session.call_tool(
                            "ListObjects",
                            {
                                "bucket": bucket_name,
                                "prefix": prefix,
                                "max_keys": 50,
                            },
                        )

                        if (
                            isinstance(objects_result, dict)
                            and "objects" in objects_result
                        ):
                            objects = objects_result["objects"]
                            print(f"\nObjects in bucket {bucket_name}:")
                            for obj in objects:
                                if isinstance(obj, dict) and "Key" in obj:
                                    print(f"- {obj['Key']}")
                        else:
                            print(f"\nObjects response: {objects_result}")
                    except Exception as e:
                        print(f"Error listing objects: {e}")

                elif choice == "5":
                    # Get object content
                    bucket_name = input("Enter bucket name: ")
                    object_key = input("Enter object key: ")

                    # Get the specified object
                    logger.info(
                        f"Retrieving object {object_key} from bucket {bucket_name}..."
                    )
                    try:
                        result = await session.call_tool(
                            "GetObject", {"bucket": bucket_name, "key": object_key}
                        )

                        # Extract content based on result type
                        if hasattr(result, "text"):
                            content = result.text
                        elif hasattr(result, "content"):
                            content = result.content
                        elif isinstance(result, dict) and "content" in result:
                            content = result["content"]
                        else:
                            content = str(result)

                        # Convert list to string if content is a list
                        if isinstance(content, list):
                            content = "\n".join(str(item) for item in content)

                        print(f"\nContent of {object_key}:")
                        print("-----------------------------------")
                        print(content[:1000] + ("..." if len(content) > 1000 else ""))
                        print("-----------------------------------")
                    except Exception as e:
                        print(f"Error retrieving object: {e}")

                elif choice == "6":
                    # Upload object
                    bucket_name = input("Enter bucket name: ")
                    new_key = input("Enter object key for the new file: ")
                    content = input("Enter content for the new file: ")

                    logger.info(f"Uploading to {bucket_name}/{new_key}...")
                    try:
                        result = await session.call_tool(
                            "PutObject",
                            {"bucket": bucket_name, "key": new_key, "content": content},
                        )
                        print(f"\nUpload result: {result}")
                    except Exception as e:
                        print(f"Error uploading object: {e}")

                elif choice == "7":
                    # Delete object
                    bucket_name = input("Enter bucket name: ")
                    key = input("Enter object key to delete: ")

                    logger.info(f"Deleting object {key} from bucket {bucket_name}...")
                    try:
                        result = await session.call_tool(
                            "DeleteObject", {"bucket": bucket_name, "key": key}
                        )
                        print(f"\nDelete result: {result}")
                    except Exception as e:
                        print(f"Error deleting object: {e}")

                elif choice == "8":
                    print("Exiting...")
                    break

                else:
                    print("Invalid choice, please try again.")


if __name__ == "__main__":
    asyncio.run(main())
