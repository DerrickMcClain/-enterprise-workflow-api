import uuid
from datetime import datetime

from pydantic import BaseModel


class AttachmentOut(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    original_filename: str
    size_bytes: int
    content_type: str | None
    kind: str
    created_at: datetime

    model_config = {"from_attributes": True}
