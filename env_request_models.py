from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute
from datetime import datetime
import os

class EnvRequestModel(Model):
    class Meta:
        table_name = os.getenv("ENV_REQUEST_TABLE", "env_requests")
        region = os.getenv("AWS_REGION", "us-east-1")
        host = os.getenv("DYNAMODB_ENDPOINT_URL", None)

    request_id = UnicodeAttribute(hash_key=True)
    env_name = UnicodeAttribute()
    env_purpose = UnicodeAttribute()
    use_case = UnicodeAttribute()
    data_domain = UnicodeAttribute()
    instance_type = UnicodeAttribute()
    ide_option = UnicodeAttribute()
    framework_option = UnicodeAttribute()
    requested_by = UnicodeAttribute()
    status = UnicodeAttribute(default="submitted")
    created_at = UnicodeAttribute(default=lambda: datetime.utcnow().isoformat())
