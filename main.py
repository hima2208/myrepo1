------ cat main.py -------

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from env_request_schemas import EnvRequestCreate
from env_request_service import create_env_request, get_all_env_requests, get_env_request_by_id
from jupyter_service import JupyterService, JupyterConfig
import uvicorn
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Environment Management API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====================================
# EXISTING ENVIRONMENT REQUEST ENDPOINTS
#
@app.post("/env-request")
def create_env(data: EnvRequestCreate):
    """Create a new environment request"""
    logger.info(f"MAIN: Creating environment request for: {data.env_name}")
    request_id = create_env_request(data)
    logger.info(f"MAIN: Successfully created environment request with ID: {request_id}")
    return {"request_id": request_id, "message": "Saved successfully"}

@app.get("/env-request")
def list_envs():
    """List all environment requests"""
    logger.info(f"MAIN: Listing all environment requests")
    result = get_all_env_requests()
    logger.info(f"MAIN: Found {len(result)} environment requests")
    return result
@app.get("/env-request/{request_id}")
def get_env(request_id: str):
    """Get specific environment request by ID"""
    logger.info(f"MAIN: Getting environment request: {request_id}")
    env = get_env_request_by_id(request_id)
    if env:
        logger.info(f"MAIN: Found environment request: {env.env_name}")
        return env.attribute_values
    logger.error(f"MAIN: Environment request not found: {request_id}")
    raise HTTPException(status_code=404, detail="Not found")

# ===================================
# DEBUG ENDPOINT
# ===================================

@app.get("/debug/test-env-request/{request_id}")
def debug_test_env_request(request_id: str):
    """Debug endpoint to test environment request lookup"""
    logger.info(f"DEBUG ENDPOINT: Testing lookup for request_id: {request_id}")
    logger.info(f"DEBUG ENDPOINT: Request ID type: {type(request_id)}")
    logger.info(f"DEBUG ENDPOINT: Request ID length: {len(request_id)}")

    try:
        # Test the service function directly
        logger.info("DEBUG ENDPOINT: Calling get_env_request_by_id...")
        env_request = get_env_request_by_id(request_id)

        if env_request:
            logger.info("DEBUG ENDPOINT: Found environment request!")
            logger.info(f"DEBUG ENDPOINT: env_name: {env_request.env_name}")
            logger.info(f"DEBUG ENDPOINT: ide_option: {env_request.ide_option}")

            return {
                "found": True,
                "request_id": env_request.request_id,
                "env_name": env_request.env_name,
                "ide_option": env_request.ide_option,
                "created_at": env_request.created_at,
                "status": getattr(env_request, 'status', 'unknown')
            }
    except Exception as e:
        logger.error(f"DEBUG ENDPOINT: Exception during lookup: {e}")
        raise HTTPException(status_code=500, detail="Internal error")
    else:
        logger.error(f"DEBUG ENDPOINT: Environment request not found!")
        # List all requests for debugging
        logger.info(f"DEBUG ENDPOINT: Fetching all requests for comparison...")
        all_requests = get_all_env_requests()
        logger.info(f"DEBUG ENDPOINT: Found {len(all_requests)} total requests")

        existing_ids = []
        for req in all_requests[:10]:  # First 10 IDs
            logger.info(f"DEBUG ENDPOINT: Existing ID: {req.request_id}")
            existing_ids.append(req.request_id)

        return {
            "found": False,
            "searched_id": request_id,
            "searched_id_length": len(request_id),
            "total_requests": len(all_requests),
            "existing_ids": existing_ids,
            "first_existing_id_length": len(existing_ids[0]) if existing_ids else 0
        }
except Exception as e:
    logger.error(f"DEBUG ENDPOINT: Exception occurred: {str(e)}")
    import traceback
    logger.error(f"DEBUG ENDPOINT: Traceback: {traceback.format_exc()}")

    return {
        "found": False,
        "error": str(e),
        "searched_id": request_id
    }

# ====================================
# JUPYTER-RELATED ENDPOINTS
# ====================================

@app.post("/generate-jupyter-url/{
    """Generate a secure presigned URL for Jupyter access"""
    logger.info(f"JUPYTER: Generating Jupyter URL for request_id: {request_id}")
    logger.info(f"JUPYTER: Request ID type: {type(request_id)}")
    logger.info(f"JUPYTER: Request ID length: {len(request_id)}")
    logger.info(f"JUPYTER: Expiry minutes: {expiry_minutes}")

    try:
        # Check Jupyter health first
        logger.info(f"JUPYTER: Checking Jupyter health...")
        jupyter_status = await JupyterService.check_jupyter_health()
        logger.info(f"JUPYTER: Jupyter status: {jupyter_status}")

        if not jupyter_status["jupyter_running"]:
            logger.error(f"JUPYTER: Jupyter service not available: {jupyter_status.get('error', 'Unknown error')}")
            raise HTTPException(
                status_code=503,
                detail=f"Jupyter service is not available: {jupyter_status.get('error', 'Unknown error')}"
            )

        # Try to get the environment request
        logger.info(f"JUPYTER: Looking up environment request: {request_id}")
        env_request = get_env_request_by_id(request_id)

        if not env_request:
            logger.error(f"JUPYTER: Environment request not found: {request_id}")

            # Additional debugging - list recent requests
            try:
                all_requests = get_all_env_requests()
                logger.info(f"JUPYTER: Total requests in DB: {len(all_requests)}")
                for req in all_requests[-5:]:  # Last 5 requests
                    logger.info(f"JUPYTER: Recent request ID: {req.request_id}")
            except Exception as e:
                logger.error(f"JUPYTER: Failed to list requests: {e}")

            raise HTTPException(
                status_code=404,
                detail=f"Environment request not found: {request_id}"
            )
    # Check if IDE option is jupyter
    if env_request.ide_option != "jupyter":
        logger.error(f"JUPYTER: IDE is not Jupyter: {env_request.ide_option}")
        raise HTTPException(
            status_code=400,
            detail=f"This environment request is not for Jupyter. IDE: {env_request.ide_option}"
        )

    # Generate presigned URL
    logger.info(f"JUPYTER: Generating presigned URL for request: {request_id}")
    logger.info("JUPYTER: Calling JupyterService.generate_presigned_url...")
    url_data = JupyterService.generate_presigned_url(
        request_id=request_id,
        expiry_minutes=expiry_minutes
    )

    logger.info("JUPYTER: Successfully generated presigned URL!")
    logger.info(f"JUPYTER: URL data: {url_data}")

    return {
        "success": True,
        "data": url_data,
        "message": f"Presigned URL generated successfully. Valid for {expiry_minutes} minutes."
    }

except HTTPException as he:
    logger.error(f"JUPYTER: HTTP Exception: {he.detail}")
    logger.error(f"JUPYTER: HTTP Status Code: {he.status_code}")
    raise
except Exception as e:
    logger.error(f"JUPYTER: Unexpected error generating presigned URL: {str(e)}")
    import traceback
    logger.error(f"JUPYTER: Traceback: {traceback.format_exc()}")
    raise HTTPException(status_code=500, detail=f"Failed to generate presigned URL: {str(e)}")
    logger.info(f"JUPYTER ACCESS: Accessing Jupyter with token: {presigned_token[:8]}...")
    try:
        result = JupyterService.validate_and_access_jupyter(presigned_token)
        logger.info("JUPYTER ACCESS: Successfully validated token, redirecting to Jupyter")
        return result
    except HTTPException as he:
        logger.error(f"JUPYTER ACCESS: HTTP Exception: {he.detail}")
        raise
    except Exception as e:
        logger.error(f"JUPYTER ACCESS: Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to access Jupyter: {str(e)}")

@app.get("/jupyter-status")
async def jupyter_status():
    """Check Jupyter service health"""
    logger.info("JUPYTER STATUS: Checking Jupyter health...")
    result = await JupyterService.check_jupyter_health()
    logger.info(f"JUPYTER STATUS: Health check result: {result}")
    return result

@app.get("/active-jupyter-sessions")
async def get_active_jupyter_sessions():
    """Get information about active Jupyter sessions"""
    logger.info("JUPYTER SESSIONS: Getting active sessions...")
    result = JupyterService.get_active_sessions()
    logger.info(f"JUPYTER SESSIONS: Found {result.get('active_sessions', 0)} active sessions")
    return result

@app.delete("/revoke-jupyter-token/{presigned_token}")
async def revoke_jupyter_token(presigned_token: str):
    """Manually revoke a specific presigned token"""
    logger.info(f"JUPYTER REVOKE: Revoking token: {presigned_token[:8]}...")
    result = JupyterService.revoke_presigned_token(presigned_token)
    logger.info("JUPYTER REVOKE: Token revoked successfully")
    return result

@app.post("/cleanup-expired-tokens")
async def cleanup_expired_tokens():
    """Clean up all expired presigned tokens"""
    logger.info("JUPYTER CLEANUP: Cleaning up expired tokens...")
    result = JupyterService.cleanup_expired_tokens()
    logger.info(f"JUPYTER CLEANUP: Cleaned up {result.get('cleaned_up', 0)} expired tokens")
    return result
@app.get("/jupyter-config")
async def get_jupyter_config():
    """Get current Jupyter configuration"""
    logger.info(f"JUPYTER CONFIG: Getting configuration...")
    result = JupyterConfig.get_config()
    logger.info(f"JUPYTER CONFIG: Configuration retrieved")
    return result

# ===================================
# HEALTH CHECK ENDPOINTS
# ===================================

@app.get("/health")
async def health_check():
    """API health check"""
    logger.info(f"HEALTH: Health check requested")
    return {"status": "healthy", "service": "Environment Management API"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Environment Management API",
        "version": "1.0.0",
        "endpoints": {
            "env_requests": "/env-request",
            "jupyter": "/jupyter-status",
            "docs": "/docs",
            "debug": "/debug/test-env-request/{request_id}"
        }
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
