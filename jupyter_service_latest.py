from fastapi import HTTPException
from fastapi.responses import RedirectResponse
import secrets
import httpx
from datetime import datetime, timedelta
from typing import Dict, Optional
from env_request_service import get_env_request_by_id
from urllib.parse import quote 

# Configuration
JUPYTER_BASE_URL = "http://10.53.136.65:8888"
JUPYTER_TOKEN = ""
PRESIGNED_URL_EXPIRY_MINUTES = 1
NOTEBOOK_REL_PATH = "notebooks/starter.ipynb"

# In-memory store for active presigned tokens (replace with Redis in production)
active_presigned_tokens: Dict[str, dict] = {}

class JupyterService:
    """Service class for handling Jupyter-related operations"""

    @staticmethod
    def generate_presigned_url(request_id: str, expiry_minutes: int = PRESIGNED_URL_EXPIRY_MINUTES) -> dict:
        """Generate a secure presigned URL for Jupyter access"""
        env_request = get_env_request_by_id(request_id)
        if not env_request:
            raise HTTPException(status_code=404, detail="Environment request not found")
        if env_request.ide_option != "jupyter":
            raise HTTPException(status_code=400, detail="This environment request is not for Jupyter")

        presigned_token = secrets.token_urlsafe(32)
        expiry_time = datetime.utcnow() + timedelta(minutes=expiry_minutes)

        active_presigned_tokens[presigned_token] = {
            "request_id": request_id,
            "env_name": env_request.env_name,
            "requested_by": getattr(env_request, "requested_by", "anonymous"),
            "created_at": datetime.utcnow(),
            "expires_at": expiry_time,
            "used_count": 0,
            "last_accessed": None
        }

        presigned_url = f"http://10.53.136.65:5000/jupyter-access/{presigned_token}"

        return {
            "presigned_url": presigned_url,
            "expires_at": expiry_time.isoformat(),
            "expires_in_minutes": expiry_minutes,
            "request_id": request_id,
            "env_name": env_request.env_name
        }

    @staticmethod
    def validate_and_access_jupyter(presigned_token: str) -> RedirectResponse:
        """Validate presigned token and redirect to Jupyter"""
        if presigned_token not in active_presigned_tokens:
            raise HTTPException(status_code=401, detail="Invalid presigned token")

        token_info = active_presigned_tokens[presigned_token]
        if datetime.utcnow() > token_info["expires_at"]:
            del active_presigned_tokens[presigned_token]
            raise HTTPException(status_code=401, detail="Presigned token has expired")

        token_info["used_count"] += 1
        token_info["last_accessed"] = datetime.utcnow()

        jupyter_url = f"{JUPYTER_BASE_URL}/lab/tree/{quote(NOTEBOOK_REL_PATH)}?token={presigned_token}"
        return RedirectResponse(url=jupyter_url, status_code=302)

    @staticmethod
    async def check_jupyter_health() -> dict:
        """Check if Jupyter service is running and accessible"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{JUPYTER_BASE_URL}/lab", timeout=5.0)
                return {
                    "jupyter_running": response.status_code == 200,
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "url": JUPYTER_BASE_URL,
                }
        except httpx.TimeoutException:
            return {
                "jupyter_running": False,
                "status": "timeout",
                "error": "Jupyter service timeout",
                "url": JUPYTER_BASE_URL
            }
        except Exception as e:
            return {
                "jupyter_running": False,
                "status": "unhealthy",
                "error": str(e),
                "url": JUPYTER_BASE_URL
            }

    @staticmethod
    def get_active_sessions() -> dict:
        """Get information about active presigned tokens"""
        now = datetime.utcnow()
        active_sessions = []
        expired_tokens = []

        for token, info in active_presigned_tokens.items():
            if now > info["expires_at"]:
                expired_tokens.append(token)
            else:
                active_sessions.append({
                    "token_preview": f"{token[:8]}...",
                    "request_id": info["request_id"],
                    "env_name": info["env_name"],
                    "requested_by": info["requested_by"],
                    "created_at": info["created_at"].isoformat(),
                    "expires_at": info["expires_at"].isoformat(),
                    "expires_in_minutes": int((info["expires_at"] - now).total_seconds() / 60),
                    "used_count": info["used_count"],
                    "last_accessed": info["last_accessed"].isoformat() if info["last_accessed"] else None
                })

        for token in expired_tokens:
            del active_presigned_tokens[token]

        return {
            "active_sessions": len(active_sessions),
            "expired_cleaned": len(expired_tokens),
            "sessions": active_sessions
        }

    @staticmethod
    def revoke_presigned_token(presigned_token: str) -> dict:
        """Manually revoke a presigned token"""
        if presigned_token not in active_presigned_tokens:
            raise HTTPException(status_code=404, detail="Presigned token not found")

        token_info = active_presigned_tokens[presigned_token]
        del active_presigned_tokens[presigned_token]

        return {
            "success": True,
            "message": "Presigned token revoked successfully",
            "revoked_token_info": {
                "request_id": token_info["request_id"],
                "env_name": token_info["env_name"],
                "was_used": token_info["used_count"] > 0
            }
        }

    @staticmethod
    def cleanup_expired_tokens() -> dict:
        """Clean up all expired tokens"""
        now = datetime.utcnow()
        expired_tokens = [token for token, info in active_presigned_tokens.items() if now > info["expires_at"]]

        for token in expired_tokens:
            del active_presigned_tokens[token]

        return {
            "cleaned_up": len(expired_tokens),
            "remaining_active": len(active_presigned_tokens)
        }

class JupyterConfig:
    """Configuration class for Jupyter settings"""

    @staticmethod
    def get_config() -> dict:
        """Get current Jupyter configuration"""
        return {
            "base_url": JUPYTER_BASE_URL,
            "default_expiry_minutes": PRESIGNED_URL_EXPIRY_MINUTES,
            "token_configured": bool(JUPYTER_TOKEN and JUPYTER_TOKEN != "your-secure-jupyter-token-123")
        }

    @staticmethod
    def update_jupyter_url(new_url: str) -> dict:
        """Update Jupyter base URL (for runtime configuration)"""
        global JUPYTER_BASE_URL
        old_url = JUPYTER_BASE_URL
        JUPYTER_BASE_URL = new_url.rstrip('/')

        return {
            "success": True,
            "message": "Jupyter URL updated",
            "old_url": old_url,
            "new_url": JUPYTER_BASE_URL
        }
