# env_request_schemas.py

from pydantic import BaseModel, Field
from typing import Optional

class EnvRequestCreate(BaseModel):
    env_name: str = Field(..., example="Data Science Sandbox")
    env_purpose: str
    use_case: str
    data_domain: str
    instance_type: str
    ide_option: str
    framework_option: Optional[str] = None
    requested_by: Optional[str] = "anonymous"
    status: Optional[str] = "submitted"

class EnvRequestRead(EnvRequestCreate):
    request_id: str
    created_at: str
