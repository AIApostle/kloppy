"""Profile and settings contracts."""

from pydantic import BaseModel, Field


class ProfileUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    workspace: str = Field(min_length=2, max_length=80)
    digest_enabled: bool
