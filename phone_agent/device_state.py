"""Device state checking utilities for Phone Agent."""

import subprocess
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from phone_agent.utils import logger, run_adb_command


class ScreenState(Enum):
    """Screen state enumeration."""

    ON = "on"
    OFF = "off"
    UNKNOWN = "unknown"


class LockState(Enum):
    """Lock screen state enumeration."""

    UNLOCKED = "unlocked"
    LOCKED = "locked"
    UNKNOWN = "unknown"


@dataclass
class DeviceState:
    """Complete device state information."""

    is_connected: bool
    screen_state: ScreenState
    lock_state: LockState
    battery_level: int | None
    current_app: str | None

    @property
    def is_ready(self) -> bool:
        """Check if device is ready for automation."""
        return (
            self.is_connected
            and self.screen_state == ScreenState.ON
            and self.lock_state == LockState.UNLOCKED
        )

    def get_issues(self) -> list[str]:
        """Get list of issues preventing automation."""
        issues = []
        if not self.is_connected:
            issues.append("Device not connected")
        if self.screen_state == ScreenState.OFF:
            issues.append("Screen is off")
        if self.lock_state == LockState.LOCKED:
            issues.append("Device is locked")
        if self.battery_level is not None and self.battery_level < 10:
            issues.append(f"Low battery: {self.battery_level}%")
        return issues


def check_device_state(device_id: str | None = None) -> DeviceState:
    """
    Check comprehensive device state before starting automation.

    Args:
        device_id: Optional device ID for multi-device setups.

    Returns:
        DeviceState object with current device information.

    Example:
        >>> state = check_device_state()
        >>> if not state.is_ready:
        ...     print("Issues:", state.get_issues())
    """
    # Check connection
    is_connected = _check_connection(device_id)
    if not is_connected:
        return DeviceState(
            is_connected=False,
            screen_state=ScreenState.UNKNOWN,
            lock_state=LockState.UNKNOWN,
            battery_level=None,
            current_app=None,
        )

    # Get all state info
    screen_state = _get_screen_state(device_id)
    lock_state = _get_lock_state(device_id)
    battery_level = _get_battery_level(device_id)
    current_app = _get_current_app(device_id)

    state = DeviceState(
        is_connected=True,
        screen_state=screen_state,
        lock_state=lock_state,
        battery_level=battery_level,
        current_app=current_app,
    )

    logger.info(
        f"Device state: connected={is_connected}, screen={screen_state.value}, "
        f"lock={lock_state.value}, battery={battery_level}%"
    )

    return state


def _check_connection(device_id: str | None = None) -> bool:
    """Check if device is connected and responding."""
    try:
        result = run_adb_command(["get-state"], device_id, timeout=5)
        return "device" in result.stdout.strip()
    except Exception as e:
        logger.debug(f"Connection check failed: {e}")
        return False


def _get_screen_state(device_id: str | None = None) -> ScreenState:
    """Get screen on/off state."""
    try:
        result = run_adb_command(
            ["shell", "dumpsys", "power", "|", "grep", "mScreenOn"],
            device_id,
            timeout=5,
        )
        output = result.stdout.lower()
        if "mscreenon=true" in output or "display power: state=on" in output:
            return ScreenState.ON
        elif "mscreenon=false" in output or "display power: state=off" in output:
            return ScreenState.OFF

        # Alternative check
        result = run_adb_command(
            ["shell", "dumpsys", "display", "|", "grep", "mScreenState"],
            device_id,
            timeout=5,
        )
        if "ON" in result.stdout:
            return ScreenState.ON
        elif "OFF" in result.stdout:
            return ScreenState.OFF

        return ScreenState.UNKNOWN
    except Exception as e:
        logger.debug(f"Screen state check failed: {e}")
        return ScreenState.UNKNOWN


def _get_lock_state(device_id: str | None = None) -> LockState:
    """Get lock screen state."""
    try:
        result = run_adb_command(
            ["shell", "dumpsys", "window", "|", "grep", "mDreamingLockscreen"],
            device_id,
            timeout=5,
        )
        if "mDreamingLockscreen=true" in result.stdout:
            return LockState.LOCKED
        elif "mDreamingLockscreen=false" in result.stdout:
            return LockState.UNLOCKED

        # Alternative: check for keyguard
        result = run_adb_command(
            ["shell", "dumpsys", "window", "|", "grep", "isShowing"],
            device_id,
            timeout=5,
        )
        if "mShowingLockscreen=true" in result.stdout:
            return LockState.LOCKED
        elif "mShowingLockscreen=false" in result.stdout:
            return LockState.UNLOCKED

        return LockState.UNKNOWN
    except Exception as e:
        logger.debug(f"Lock state check failed: {e}")
        return LockState.UNKNOWN


def _get_battery_level(device_id: str | None = None) -> int | None:
    """Get battery level percentage."""
    try:
        result = run_adb_command(
            ["shell", "dumpsys", "battery", "|", "grep", "level"], device_id, timeout=5
        )
        for line in result.stdout.split("\n"):
            if "level:" in line.lower():
                level_str = line.split(":")[-1].strip()
                return int(level_str)
        return None
    except Exception as e:
        logger.debug(f"Battery check failed: {e}")
        return None


def _get_current_app(device_id: str | None = None) -> str | None:
    """Get current foreground app package name."""
    try:
        result = run_adb_command(
            ["shell", "dumpsys", "window", "|", "grep", "mCurrentFocus"],
            device_id,
            timeout=5,
        )
        output = result.stdout
        if "/" in output:
            # Extract package name from format: Window{... com.example.app/...}
            start = output.find("{")
            end = output.find("/")
            if start != -1 and end != -1:
                parts = output[start:end].split()
                if parts:
                    return parts[-1]
        return None
    except Exception as e:
        logger.debug(f"Current app check failed: {e}")
        return None


def wake_screen(device_id: str | None = None) -> bool:
    """
    Wake up the screen if it's off.

    Args:
        device_id: Optional device ID.

    Returns:
        True if successful.
    """
    try:
        run_adb_command(["shell", "input", "keyevent", "KEYCODE_WAKEUP"], device_id)
        logger.info("Screen wake command sent")
        return True
    except Exception as e:
        logger.error(f"Failed to wake screen: {e}")
        return False


def unlock_screen(device_id: str | None = None, swipe_up: bool = True) -> bool:
    """
    Attempt to unlock the screen with swipe gesture.

    Args:
        device_id: Optional device ID.
        swipe_up: If True, swipe up to unlock.

    Returns:
        True if command was sent (unlock success not guaranteed).

    Note:
        This only works for swipe-to-unlock. PIN/pattern locks
        require manual intervention.
    """
    try:
        if swipe_up:
            run_adb_command(
                ["shell", "input", "swipe", "500", "1800", "500", "500", "300"],
                device_id,
            )
        logger.info("Unlock swipe sent")
        return True
    except Exception as e:
        logger.error(f"Failed to unlock: {e}")
        return False
