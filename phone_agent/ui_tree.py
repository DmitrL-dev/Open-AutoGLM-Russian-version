"""UI Tree parsing using Android uiautomator.

Provides precise element detection by parsing the UI hierarchy XML,
instead of relying solely on coordinate-based interactions.
"""

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Optional

from phone_agent.utils import run_adb_command, logger


@dataclass
class UIElement:
    """Represents a UI element from the Android view hierarchy."""

    resource_id: str = ""
    class_name: str = ""
    text: str = ""
    content_desc: str = ""
    bounds: tuple[int, int, int, int] = (0, 0, 0, 0)  # left, top, right, bottom
    clickable: bool = False
    scrollable: bool = False
    focusable: bool = False
    enabled: bool = True
    selected: bool = False
    checked: bool = False
    children: list["UIElement"] = field(default_factory=list)

    @property
    def center(self) -> tuple[int, int]:
        """Get center coordinates of the element."""
        left, top, right, bottom = self.bounds
        return ((left + right) // 2, (top + bottom) // 2)

    @property
    def center_normalized(self) -> tuple[int, int]:
        """Get center coordinates normalized to 0-999 range."""
        x, y = self.center
        # Assuming 1080x1920 screen, normalize to 0-999
        return (min(999, x * 999 // 1080), min(999, y * 999 // 1920))

    @property
    def display_text(self) -> str:
        """Get displayable text (text or content-desc)."""
        return self.text or self.content_desc or self.resource_id.split("/")[-1]

    def matches(
        self,
        text: Optional[str] = None,
        resource_id: Optional[str] = None,
        class_name: Optional[str] = None,
        content_desc: Optional[str] = None,
        clickable: Optional[bool] = None,
    ) -> bool:
        """Check if element matches given criteria."""
        if text and text.lower() not in self.text.lower():
            return False
        if resource_id and resource_id not in self.resource_id:
            return False
        if class_name and class_name not in self.class_name:
            return False
        if content_desc and content_desc.lower() not in self.content_desc.lower():
            return False
        if clickable is not None and self.clickable != clickable:
            return False
        return True


@dataclass
class UITree:
    """Parsed UI hierarchy tree."""

    root: Optional[UIElement] = None
    screen_width: int = 1080
    screen_height: int = 1920

    def find_all(
        self,
        text: Optional[str] = None,
        resource_id: Optional[str] = None,
        class_name: Optional[str] = None,
        content_desc: Optional[str] = None,
        clickable: Optional[bool] = None,
    ) -> list[UIElement]:
        """Find all elements matching criteria."""
        results = []

        def search(element: UIElement):
            if element.matches(text, resource_id, class_name, content_desc, clickable):
                results.append(element)
            for child in element.children:
                search(child)

        if self.root:
            search(self.root)
        return results

    def find_one(self, **kwargs) -> Optional[UIElement]:
        """Find first element matching criteria."""
        results = self.find_all(**kwargs)
        return results[0] if results else None

    def find_by_text(self, text: str, exact: bool = False) -> list[UIElement]:
        """Find elements by text content."""
        results = []

        def search(element: UIElement):
            if exact:
                if element.text == text or element.content_desc == text:
                    results.append(element)
            else:
                if (
                    text.lower() in element.text.lower()
                    or text.lower() in element.content_desc.lower()
                ):
                    results.append(element)
            for child in element.children:
                search(child)

        if self.root:
            search(self.root)
        return results

    def get_clickable_elements(self) -> list[UIElement]:
        """Get all clickable elements."""
        return self.find_all(clickable=True)

    def get_input_fields(self) -> list[UIElement]:
        """Get all input fields (EditText)."""
        return self.find_all(class_name="EditText")


def dump_ui_hierarchy(device_id: Optional[str] = None) -> str:
    """
    Dump UI hierarchy XML from device.

    Args:
        device_id: Optional device ID.

    Returns:
        XML string of UI hierarchy.
    """
    # Dump to device
    result = run_adb_command(
        ["shell", "uiautomator", "dump", "/sdcard/ui_dump.xml"], device_id, timeout=15
    )

    if (
        "UI hierchary dumped" not in result.stdout
        and "dumped to" not in result.stdout.lower()
    ):
        logger.warning(f"UI dump may have failed: {result.stdout}")

    # Pull content
    result = run_adb_command(
        ["shell", "cat", "/sdcard/ui_dump.xml"], device_id, timeout=10
    )

    return result.stdout


def parse_ui_tree(xml_content: str) -> UITree:
    """
    Parse UI hierarchy XML into UITree structure.

    Args:
        xml_content: XML string from uiautomator dump.

    Returns:
        Parsed UITree object.
    """
    tree = UITree()

    try:
        root = ET.fromstring(xml_content)
        tree.root = _parse_element(root)
    except ET.ParseError as e:
        logger.error(f"Failed to parse UI XML: {e}")

    return tree


def _parse_element(node: ET.Element) -> UIElement:
    """Parse single XML node into UIElement."""

    # Parse bounds "[left,top][right,bottom]"
    bounds_str = node.get("bounds", "[0,0][0,0]")
    bounds_match = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds_str)
    if bounds_match:
        bounds = tuple(int(x) for x in bounds_match.groups())
    else:
        bounds = (0, 0, 0, 0)

    element = UIElement(
        resource_id=node.get("resource-id", ""),
        class_name=node.get("class", ""),
        text=node.get("text", ""),
        content_desc=node.get("content-desc", ""),
        bounds=bounds,
        clickable=node.get("clickable", "false") == "true",
        scrollable=node.get("scrollable", "false") == "true",
        focusable=node.get("focusable", "false") == "true",
        enabled=node.get("enabled", "true") == "true",
        selected=node.get("selected", "false") == "true",
        checked=node.get("checked", "false") == "true",
    )

    # Parse children
    for child in node:
        element.children.append(_parse_element(child))

    return element


def get_ui_tree(device_id: Optional[str] = None) -> UITree:
    """
    Get current UI tree from device.

    Convenience function that dumps and parses in one call.

    Args:
        device_id: Optional device ID.

    Returns:
        Parsed UITree.

    Example:
        >>> tree = get_ui_tree()
        >>> button = tree.find_one(text="Submit", clickable=True)
        >>> if button:
        ...     print(f"Found at {button.center}")
    """
    xml = dump_ui_hierarchy(device_id)
    return parse_ui_tree(xml)


def find_element_coordinates(
    text: Optional[str] = None,
    resource_id: Optional[str] = None,
    device_id: Optional[str] = None,
) -> Optional[tuple[int, int]]:
    """
    Find element and return its center coordinates.

    Args:
        text: Text to search for.
        resource_id: Resource ID to search for.
        device_id: Optional device ID.

    Returns:
        (x, y) center coordinates or None if not found.
    """
    tree = get_ui_tree(device_id)
    element = tree.find_one(text=text, resource_id=resource_id)

    if element:
        return element.center
    return None
