"""
Netlify Functions wrapper for FastAPI application
"""
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from mangum import Mangum

    from app.main import app

    # Create the Mangum handler for Netlify Functions
    handler = Mangum(app, lifespan="off")

except ImportError as import_error:
    print(f"Import error: {import_error}")
    error_message = str(import_error)

    # Fallback handler for debugging
    def handler(event, context):
        return {"statusCode": 500, "body": f"Import error: {error_message}"}
