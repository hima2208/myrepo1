from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from env_request_schemas import EnvRequestCreate
from env_request_service import create_env_request, get_all_env_requests, get_env_request_by_id
from jupyter_service import JupyterService, JupyterConfig
import uvicorn
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Environment Management API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment request endpoints
@app.post("/env-request")
def create_env(data: EnvRequestCreate):
    """Create a new environment request"""
    logger.info(f"Creating environment request: {data.env_name}")
    try:
        request_id = create_env_request(data)
        return {"request_id": request_id, "message": "Saved successfully"}
    except Exception as e:
        logger.error(f"Error creating environment request: {e}")
        raise HTTPException(status_code=500, detail="Failed to create environment request")

@app.get("/env-request")
def list_envs():
    """List all environment requests"""
    logger.info("Listing all environment requests")
    return get_all_env_requests()

@app.get("/env-request/{request_id}")
def get_env(request_id: str):
    """Get specific environment request by ID"""
    logger.info(f"Retrieving environment request: {request_id}")
    env = get_env_request_by_id(request_id)
    if not env:
        logger.warning(f"Environment request not found: {request_id}")
        raise HTTPException(status_code=404, detail="Not found")
    return env.attribute_values

# Jupyter-related endpoints
@app.post("/generate-jupyter-url/{request_id}")
async def generate_jupyter_url(request_id: str, expiry_minutes: int = 60):
    """Generate a secure presigned URL for Jupyter access"""
    logger.info(f"Generating Jupyter URL for request_id: {request_id}")
    try:
        health = await JupyterService.check_jupyter_health()
        if not health.get("jupyter_running"):
            logger.error("Jupyter service is unavailable")
            raise HTTPException(status_code=503, detail="Jupyter service unavailable")

        env = get_env_request_by_id(request_id)
        if not env:
            logger.error(f"Environment request not found: {request_id}")
            raise HTTPException(status_code=404, detail="Environment request not found")
        if env.ide_option != "jupyter":
            logger.error(f"IDE option is not jupyter: {env.ide_option}")
            raise HTTPException(status_code=400, detail="IDE option must be 'jupyter'")

        url_data = JupyterService.generate_presigned_url(
            request_id=request_id,
            expiry_minutes=expiry_minutes
        )
        return {"success": True, "data": url_data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating Jupyter URL: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/jupyter-status")
async def jupyter_status():
    """Check Jupyter service health"""
    return await JupyterService.check_jupyter_health()

@app.get("/active-jupyter-sessions")
async def get_active_jupyter_sessions():
    """Get information about active Jupyter sessions"""
    return JupyterService.get_active_sessions()

@app.delete("/revoke-jupyter-token/{token}")
def revoke_jupyter_token(token: str):
    """Manually revoke a specific presigned token"""
    return JupyterService.revoke_presigned_token(token)

@app.post("/cleanup-expired-tokens")
def cleanup_expired_tokens():
    """Clean up all expired presigned tokens"""
    return JupyterService.cleanup_expired_tokens()

@app.get("/jupyter-config")
def get_jupyter_config():
    """Get current Jupyter configuration"""
    return JupyterConfig.get_config()

# Health check
@app.get("/health")
def health_check():
    """API health check"""
    return {"status": "healthy", "service": "Environment Management API"}

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Environment Management API",
        "version": "1.0.0",
        "endpoints": {
            "env_requests": "/env-request",
            "jupyter_status": "/jupyter-status",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000)
