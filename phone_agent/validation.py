"""Response validation utilities for Phone Agent."""

from dataclasses import dataclass
from typing import Any

from phone_agent.utils import logger


@dataclass
class ValidationResult:
    """Result of response validation."""

    is_valid: bool
    errors: list[str]
    warnings: list[str]

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


# Valid action names
VALID_ACTIONS = {
    "Launch",
    "Tap",
    "Type",
    "Type_Name",
    "Swipe",
    "Back",
    "Home",
    "Double Tap",
    "Long Press",
    "Wait",
    "Take_over",
    "Note",
    "Call_API",
    "Interact",
}

# Actions that require specific fields
ACTION_REQUIREMENTS = {
    "Launch": ["app"],
    "Tap": ["element"],
    "Type": ["text"],
    "Type_Name": ["text"],
    "Swipe": ["start", "end"],
    "Double Tap": ["element"],
    "Long Press": ["element"],
    "Wait": ["duration"],
}


def validate_action(action: dict[str, Any]) -> ValidationResult:
    """
    Validate a parsed action dictionary.

    Args:
        action: Parsed action from model response.

    Returns:
        ValidationResult with errors and warnings.

    Example:
        >>> from phone_agent.actions.handler import parse_action
        >>> action = parse_action('do(action="Tap", element=[100, 200])')
        >>> result = validate_action(action)
        >>> if not result.is_valid:
        ...     print("Errors:", result.errors)
    """
    errors = []
    warnings = []

    # Check metadata
    metadata = action.get("_metadata")
    if metadata not in ("do", "finish"):
        errors.append(f"Invalid _metadata: {metadata}")
        return ValidationResult(False, errors, warnings)

    # Finish action only needs message
    if metadata == "finish":
        if "message" not in action:
            warnings.append("finish action without message")
        return ValidationResult(True, errors, warnings)

    # Validate action name
    action_name = action.get("action")
    if action_name is None:
        errors.append("Missing 'action' field")
        return ValidationResult(False, errors, warnings)

    if action_name not in VALID_ACTIONS:
        errors.append(f"Unknown action: {action_name}")
        return ValidationResult(False, errors, warnings)

    # Check required fields
    required_fields = ACTION_REQUIREMENTS.get(action_name, [])
    for field in required_fields:
        if field not in action:
            errors.append(
                f"Missing required field '{field}' for action '{action_name}'"
            )

    # Validate coordinates
    if "element" in action:
        element = action["element"]
        coord_errors = _validate_coordinates(element, "element")
        errors.extend(coord_errors)

    if "start" in action:
        coord_errors = _validate_coordinates(action["start"], "start")
        errors.extend(coord_errors)

    if "end" in action:
        coord_errors = _validate_coordinates(action["end"], "end")
        errors.extend(coord_errors)

    # Validate Wait duration
    if action_name == "Wait" and "duration" in action:
        duration_str = str(action["duration"])
        try:
            # Extract number from "5 seconds" or just "5"
            num = float(duration_str.replace("seconds", "").replace("s", "").strip())
            if num < 0:
                errors.append("Wait duration cannot be negative")
            elif num > 60:
                warnings.append(f"Long wait duration: {num}s")
        except ValueError:
            errors.append(f"Invalid duration format: {duration_str}")

    is_valid = len(errors) == 0

    if not is_valid:
        logger.warning(f"Action validation failed: {errors}")
    elif warnings:
        logger.debug(f"Action validation warnings: {warnings}")

    return ValidationResult(is_valid, errors, warnings)


def _validate_coordinates(coords: Any, field_name: str) -> list[str]:
    """Validate coordinate array."""
    errors = []

    if not isinstance(coords, (list, tuple)):
        errors.append(f"{field_name} must be a list, got {type(coords).__name__}")
        return errors

    if len(coords) != 2:
        errors.append(f"{field_name} must have 2 values, got {len(coords)}")
        return errors

    for i, val in enumerate(coords):
        if not isinstance(val, (int, float)):
            errors.append(
                f"{field_name}[{i}] must be a number, got {type(val).__name__}"
            )
        elif val < 0 or val > 999:
            errors.append(f"{field_name}[{i}]={val} out of range (0-999)")

    return errors


def sanitize_action(action: dict[str, Any]) -> dict[str, Any]:
    """
    Sanitize and fix common issues in action dictionary.

    Args:
        action: Parsed action that may have issues.

    Returns:
        Sanitized action dictionary.
    """
    sanitized = action.copy()

    # Clamp coordinates to valid range
    for field in ("element", "start", "end"):
        if field in sanitized and isinstance(sanitized[field], list):
            sanitized[field] = [max(0, min(999, int(v))) for v in sanitized[field]]

    # Normalize action names
    action_name = sanitized.get("action", "")

    # Fix common typos
    typo_fixes = {
        "tap": "Tap",
        "TAP": "Tap",
        "swipe": "Swipe",
        "SWIPE": "Swipe",
        "launch": "Launch",
        "LAUNCH": "Launch",
        "back": "Back",
        "BACK": "Back",
        "home": "Home",
        "HOME": "Home",
        "type": "Type",
        "TYPE": "Type",
    }

    if action_name in typo_fixes:
        sanitized["action"] = typo_fixes[action_name]
        logger.debug(f"Fixed action name: {action_name} -> {sanitized['action']}")

    return sanitized
