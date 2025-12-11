"""Pydantic models for type-safe configuration and validation."""

from enum import Enum
from typing import Optional, Callable, Any
from pydantic import BaseModel, Field, field_validator, model_validator


class Language(str, Enum):
    """Supported languages."""

    ENGLISH = "en"
    RUSSIAN = "ru"


class ActionType(str, Enum):
    """Valid action types."""

    LAUNCH = "Launch"
    TAP = "Tap"
    TYPE = "Type"
    TYPE_NAME = "Type_Name"
    SWIPE = "Swipe"
    BACK = "Back"
    HOME = "Home"
    DOUBLE_TAP = "Double Tap"
    LONG_PRESS = "Long Press"
    WAIT = "Wait"
    TAKE_OVER = "Take_over"
    NOTE = "Note"
    CALL_API = "Call_API"
    INTERACT = "Interact"


class Coordinates(BaseModel):
    """Screen coordinates with validation."""

    x: int = Field(ge=0, le=999, description="X coordinate (0-999)")
    y: int = Field(ge=0, le=999, description="Y coordinate (0-999)")

    def to_list(self) -> list[int]:
        return [self.x, self.y]

    @classmethod
    def from_list(cls, coords: list[int]) -> "Coordinates":
        return cls(x=coords[0], y=coords[1])


class ModelConfigPydantic(BaseModel):
    """Configuration for the AI model connection."""

    base_url: str = Field(
        default="http://localhost:8000/v1",
        description="Base URL of the OpenAI-compatible API",
    )
    model_name: str = Field(
        default="autoglm-phone-9b", description="Name of the model to use"
    )
    api_key: str = Field(default="EMPTY", description="API key for authentication")
    temperature: float = Field(
        default=0.1, ge=0.0, le=2.0, description="Sampling temperature"
    )
    max_tokens: int = Field(
        default=1024, ge=1, le=32768, description="Maximum tokens in response"
    )
    timeout: int = Field(default=60, ge=1, description="Request timeout in seconds")

    class Config:
        extra = "forbid"


class AgentConfigPydantic(BaseModel):
    """Configuration for the Phone Agent behavior."""

    max_steps: int = Field(
        default=100, ge=1, le=1000, description="Maximum steps before stopping"
    )
    device_id: Optional[str] = Field(
        default=None, description="ADB device ID (None for default device)"
    )
    lang: Language = Field(
        default=Language.ENGLISH, description="Language for prompts and UI"
    )
    verbose: bool = Field(default=True, description="Enable verbose output")
    check_device_state: bool = Field(
        default=True, description="Check device state before running"
    )
    use_ui_tree: bool = Field(
        default=False, description="Use UI tree for element detection"
    )
    retry_count: int = Field(
        default=3, ge=0, le=10, description="Number of retries for failed actions"
    )
    step_delay: float = Field(
        default=0.5, ge=0.0, le=10.0, description="Delay between steps in seconds"
    )

    class Config:
        extra = "forbid"


class ActionRequest(BaseModel):
    """Validated action request from model."""

    action: ActionType
    element: Optional[Coordinates] = None
    start: Optional[Coordinates] = None
    end: Optional[Coordinates] = None
    text: Optional[str] = None
    app: Optional[str] = None
    message: Optional[str] = None
    duration: Optional[str] = None
    instruction: Optional[str] = None

    @model_validator(mode="after")
    def validate_required_fields(self) -> "ActionRequest":
        """Validate that required fields are present for each action type."""
        action = self.action

        if action == ActionType.TAP and self.element is None:
            raise ValueError("Tap action requires 'element' coordinates")
        if action == ActionType.SWIPE and (self.start is None or self.end is None):
            raise ValueError("Swipe action requires 'start' and 'end' coordinates")
        if action in (ActionType.TYPE, ActionType.TYPE_NAME) and self.text is None:
            raise ValueError(f"{action.value} action requires 'text'")
        if action == ActionType.LAUNCH and self.app is None:
            raise ValueError("Launch action requires 'app' name")
        if action == ActionType.DOUBLE_TAP and self.element is None:
            raise ValueError("Double Tap action requires 'element' coordinates")
        if action == ActionType.LONG_PRESS and self.element is None:
            raise ValueError("Long Press action requires 'element' coordinates")

        return self

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for handler."""
        result = {"action": self.action.value, "_metadata": "do"}

        if self.element:
            result["element"] = self.element.to_list()
        if self.start:
            result["start"] = self.start.to_list()
        if self.end:
            result["end"] = self.end.to_list()
        if self.text:
            result["text"] = self.text
        if self.app:
            result["app"] = self.app
        if self.message:
            result["message"] = self.message
        if self.duration:
            result["duration"] = self.duration
        if self.instruction:
            result["instruction"] = self.instruction

        return result


class FinishRequest(BaseModel):
    """Validated finish request from model."""

    message: str = Field(description="Completion message")

    def to_dict(self) -> dict[str, Any]:
        return {"_metadata": "finish", "message": self.message}


class APIConfig(BaseModel):
    """Configuration for REST API server."""

    host: str = Field(
        default="127.0.0.1",
        description="Host to bind (use 127.0.0.1 for localhost only)",
    )
    port: int = Field(default=8080, ge=1024, le=65535, description="Port to listen on")
    api_key: Optional[str] = Field(
        default=None, description="API key for authentication (None to disable)"
    )
    rate_limit: int = Field(default=60, ge=1, description="Max requests per minute")
    allowed_actions: list[ActionType] = Field(
        default_factory=lambda: list(ActionType),
        description="Whitelist of allowed actions",
    )
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"],
        description="Allowed CORS origins",
    )

    @field_validator("host")
    @classmethod
    def validate_host(cls, v: str) -> str:
        if v not in ("127.0.0.1", "localhost", "0.0.0.0"):
            raise ValueError("Host must be 127.0.0.1, localhost, or 0.0.0.0")
        if v == "0.0.0.0":
            import warnings

            warnings.warn(
                "Binding to 0.0.0.0 exposes the API to the network. "
                "Ensure proper authentication is configured.",
                UserWarning,
            )
        return v


class WebUIConfig(BaseModel):
    """Configuration for Web UI."""

    enabled: bool = Field(default=True)
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=3000, ge=1024, le=65535)
    require_auth: bool = Field(default=True)
    username: str = Field(default="admin")
    password: Optional[str] = Field(default=None)  # Must be set if require_auth


def create_model_config(**kwargs) -> ModelConfigPydantic:
    """Create validated model config."""
    return ModelConfigPydantic(**kwargs)


def create_agent_config(**kwargs) -> AgentConfigPydantic:
    """Create validated agent config."""
    return AgentConfigPydantic(**kwargs)
