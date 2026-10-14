"""Profile and execution-policy settings contracts."""

from typing import Literal

from pydantic import BaseModel, Field


class UserSettings(BaseModel):
    name: str = Field(default="", min_length=0, max_length=80)
    workspace: str = Field(default="", max_length=120)
    digest_enabled: bool = True
    permission_policy: Literal["ask", "auto"] = "ask"


class ProfileUpdate(UserSettings):
    name: str = Field(min_length=2, max_length=80)
    workspace: str = Field(min_length=2, max_length=120)
