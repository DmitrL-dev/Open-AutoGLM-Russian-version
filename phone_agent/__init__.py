"""
Phone Agent - An AI-powered phone automation framework.

This package provides tools for automating Android phone interactions
using AI models for visual understanding and decision making.

Security-hardened fork with Russian/English localization.
"""

from phone_agent.agent import PhoneAgent

# Device state utilities
from phone_agent.device_state import (
    DeviceState,
    check_device_state,
    wake_screen,
    unlock_screen,
)

# Logging and retry utilities
from phone_agent.utils import setup_logging, retry, logger

# Validation
from phone_agent.validation import validate_action, sanitize_action

# UI Tree parsing
from phone_agent.ui_tree import (
    UITree,
    UIElement,
    get_ui_tree,
    find_element_coordinates,
)

# Pydantic models
from phone_agent.models import (
    ModelConfigPydantic,
    AgentConfigPydantic,
    ActionRequest,
    ActionType,
    Coordinates,
    APIConfig,
)

__version__ = "0.3.0"
__all__ = [
    # Core
    "PhoneAgent",
    # Device
    "DeviceState",
    "check_device_state",
    "wake_screen",
    "unlock_screen",
    # Utils
    "setup_logging",
    "retry",
    "logger",
    # Validation
    "validate_action",
    "sanitize_action",
    # UI Tree
    "UITree",
    "UIElement",
    "get_ui_tree",
    "find_element_coordinates",
    # Models
    "ModelConfigPydantic",
    "AgentConfigPydantic",
    "ActionRequest",
    "ActionType",
    "Coordinates",
    "APIConfig",
]
