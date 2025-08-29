import time
import json
import logging
from fastapi import Request

logger = logging.getLogger(__name__)

async def log_requests(request: Request, call_next):
    """
    Middleware to log incoming HTTP requests and their responses.
    Logs request method, URL, client IP, request body (if available), 
    response status code, and processing time.
    """
    start_time = time.time()
    
    method = request.method
    url = str(request.url)
    client_host = request.client.host if request.client else "unknown"
    
    logger.info(f"Request: {method} {url} from {client_host}")
    
    try:
        body = await request.body()
        if body:
            body_str = body.decode('utf-8')
            try:
                body_json = json.loads(body_str)
                # logger.info(f"Request body: {json.dumps(body_json, indent=2)}")
            except json.JSONDecodeError:
                # logger.info(f"Request body: {body_str}")
                pass
    except Exception as e:
        logger.warning(f"Could not log request body: {str(e)}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} processed in {process_time:.4f} seconds")
    
    return response
