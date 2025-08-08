from env_request_models import EnvRequestModel
from env_request_schemas import EnvRequestCreate
import uuid
from datetime import datetime

def create_env_request(data: EnvRequestCreate) -> str:
    """Create and save a new environment request"""
    request_id = str(uuid.uuid4())
    item = EnvRequestModel(
        request_id=request_id,
        created_at=datetime.utcnow().isoformat(),
        **data.dict()
    )
    item.save()
    return request_id

def get_all_env_requests():
    """Retrieve all environment requests"""
    return list(EnvRequestModel.scan())

def get_env_request_by_id(request_id: str):
    """Retrieve a single environment request by ID"""
    try:
        return EnvRequestModel.get(request_id)
    except EnvRequestModel.DoesNotExist:
        return None
