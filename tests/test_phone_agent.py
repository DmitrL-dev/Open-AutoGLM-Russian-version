"""Unit tests for Phone Agent."""

import pytest
from unittest.mock import MagicMock, patch

from phone_agent.actions.handler import parse_action, _safe_parse_do_action
from phone_agent.validation import validate_action, sanitize_action, ValidationResult
from phone_agent.models import (
    ActionRequest,
    ActionType,
    Coordinates,
    ModelConfigPydantic,
    AgentConfigPydantic,
    APIConfig,
)


class TestSafeParser:
    """Tests for the safe action parser (eval replacement)."""

    def test_parse_tap_action(self):
        """Test parsing Tap action."""
        result = parse_action('do(action="Tap", element=[100, 200])')

        assert result["_metadata"] == "do"
        assert result["action"] == "Tap"
        assert result["element"] == [100, 200]

    def test_parse_swipe_action(self):
        """Test parsing Swipe action with start and end."""
        result = parse_action('do(action="Swipe", start=[0, 500], end=[0, 100])')

        assert result["action"] == "Swipe"
        assert result["start"] == [0, 500]
        assert result["end"] == [0, 100]

    def test_parse_type_action(self):
        """Test parsing Type action with text."""
        result = parse_action('do(action="Type", text="Hello World")')

        assert result["action"] == "Type"
        assert result["text"] == "Hello World"

    def test_parse_launch_action(self):
        """Test parsing Launch action."""
        result = parse_action('do(action="Launch", app="Chrome")')

        assert result["action"] == "Launch"
        assert result["app"] == "Chrome"

    def test_parse_finish_action(self):
        """Test parsing finish action."""
        result = parse_action('finish(message="Task completed successfully")')

        assert result["_metadata"] == "finish"
        assert result["message"] == "Task completed successfully"

    def test_parse_back_action(self):
        """Test parsing simple Back action."""
        result = parse_action('do(action="Back")')

        assert result["action"] == "Back"

    def test_reject_malicious_code(self):
        """Test that malicious code is NOT executed."""
        # This would execute os.system if eval was used
        malicious = 'do(action="Tap") or __import__("os").system("echo hacked")'

        # Should parse but not execute the malicious part
        result = _safe_parse_do_action(malicious)

        # Should only get the action, not execute os.system
        assert result.get("action") == "Tap"
        assert "__import__" not in str(result)

    def test_invalid_format_raises(self):
        """Test that invalid format raises ValueError."""
        with pytest.raises(ValueError):
            parse_action("invalid format")

    def test_parse_single_quotes(self):
        """Test parsing with single quotes."""
        result = parse_action("do(action='Tap', element=[50, 50])")

        assert result["action"] == "Tap"


class TestValidation:
    """Tests for action validation."""

    def test_valid_tap_action(self):
        """Test validation of valid Tap action."""
        action = {"_metadata": "do", "action": "Tap", "element": [100, 200]}

        result = validate_action(action)

        assert result.is_valid
        assert len(result.errors) == 0

    def test_invalid_coordinates_range(self):
        """Test validation rejects out-of-range coordinates."""
        action = {
            "_metadata": "do",
            "action": "Tap",
            "element": [1500, 200],  # 1500 > 999
        }

        result = validate_action(action)

        assert not result.is_valid
        assert any("out of range" in e for e in result.errors)

    def test_missing_required_field(self):
        """Test validation catches missing required field."""
        action = {
            "_metadata": "do",
            "action": "Tap",
            # Missing "element"
        }

        result = validate_action(action)

        assert not result.is_valid
        assert any("element" in e for e in result.errors)

    def test_unknown_action(self):
        """Test validation rejects unknown action."""
        action = {"_metadata": "do", "action": "UnknownAction"}

        result = validate_action(action)

        assert not result.is_valid

    def test_sanitize_fixes_case(self):
        """Test sanitize fixes action name case."""
        action = {"action": "tap", "element": [100, 200]}

        result = sanitize_action(action)

        assert result["action"] == "Tap"

    def test_sanitize_clamps_coordinates(self):
        """Test sanitize clamps coordinates to valid range."""
        action = {"action": "Tap", "element": [1500, -50]}

        result = sanitize_action(action)

        assert result["element"] == [999, 0]


class TestPydanticModels:
    """Tests for Pydantic configuration models."""

    def test_model_config_defaults(self):
        """Test ModelConfig has sensible defaults."""
        config = ModelConfigPydantic()

        assert config.base_url == "http://localhost:8000/v1"
        assert config.temperature == 0.1
        assert config.api_key == "EMPTY"

    def test_model_config_validation(self):
        """Test ModelConfig validates temperature range."""
        with pytest.raises(ValueError):
            ModelConfigPydantic(temperature=3.0)  # Max is 2.0

    def test_agent_config_defaults(self):
        """Test AgentConfig defaults."""
        config = AgentConfigPydantic()

        assert config.max_steps == 100
        assert config.check_device_state is True

    def test_api_config_localhost_warning(self):
        """Test APIConfig warns on 0.0.0.0."""
        with pytest.warns(UserWarning, match="exposes the API"):
            APIConfig(host="0.0.0.0")

    def test_api_config_rejects_external_host(self):
        """Test APIConfig rejects arbitrary hosts."""
        with pytest.raises(ValueError):
            APIConfig(host="192.168.1.100")

    def test_coordinates_validation(self):
        """Test Coordinates validates range."""
        coords = Coordinates(x=500, y=500)
        assert coords.to_list() == [500, 500]

        with pytest.raises(ValueError):
            Coordinates(x=1000, y=500)  # x > 999

    def test_action_request_validation(self):
        """Test ActionRequest validates required fields."""
        # Valid
        action = ActionRequest(action=ActionType.TAP, element=Coordinates(x=100, y=200))
        assert action.action == ActionType.TAP

        # Invalid: Tap without element
        with pytest.raises(ValueError):
            ActionRequest(action=ActionType.TAP)


class TestUITree:
    """Tests for UI Tree parsing."""

    def test_parse_simple_element(self):
        """Test parsing simple UI element."""
        from phone_agent.ui_tree import parse_ui_tree, UIElement

        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <hierarchy>
            <node class="android.widget.Button" 
                  text="Submit" 
                  bounds="[100,200][300,250]"
                  clickable="true" />
        </hierarchy>
        """

        tree = parse_ui_tree(xml)

        assert tree.root is not None
        # First child should be the button
        button = tree.root.children[0] if tree.root.children else tree.root
        assert "Button" in button.class_name or button.text == "Submit"

    def test_find_by_text(self):
        """Test finding element by text."""
        from phone_agent.ui_tree import parse_ui_tree

        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <hierarchy>
            <node text="Cancel" bounds="[0,0][100,50]" clickable="true" />
            <node text="Submit" bounds="[200,0][300,50]" clickable="true" />
        </hierarchy>
        """

        tree = parse_ui_tree(xml)
        results = tree.find_by_text("Submit")

        assert len(results) >= 1
        assert any(el.text == "Submit" for el in results)


# Run with: pytest tests/test_phone_agent.py -v
