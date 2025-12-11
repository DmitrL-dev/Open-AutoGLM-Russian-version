"""
Phone Agent - An AI-powered phone automation framework.

This package provides tools for automating Android phone interactions
using AI models for visual understanding and decision making.
"""

from phone_agent.agent import PhoneAgent
from phone_agent.device_state import (
    DeviceState,
    check_device_state,
    wake_screen,
    unlock_screen,
)
from phone_agent.utils import setup_logging, retry, logger
from phone_agent.validation import validate_action, sanitize_action

__version__ = "0.2.0"
__all__ = [
    "PhoneAgent",
    "DeviceState",
    "check_device_state",
    "wake_screen",
    "unlock_screen",
    "setup_logging",
    "retry",
    "logger",
    "validate_action",
    "sanitize_action",
]
