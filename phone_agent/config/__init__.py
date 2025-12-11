"""Configuration module for Phone Agent."""

from phone_agent.config.apps import APP_PACKAGES
from phone_agent.config.i18n import get_message, get_messages
from phone_agent.config.prompts_en import SYSTEM_PROMPT as SYSTEM_PROMPT_EN
from phone_agent.config.prompts_ru import SYSTEM_PROMPT as SYSTEM_PROMPT_RU


def get_system_prompt(lang: str = "en") -> str:
    """
    Get system prompt by language.

    Args:
        lang: Language code, 'ru' for Russian, 'en' for English.

    Returns:
        System prompt string.
    """
    if lang == "ru":
        return SYSTEM_PROMPT_RU
    return SYSTEM_PROMPT_EN


# Default to English
SYSTEM_PROMPT = SYSTEM_PROMPT_EN

__all__ = [
    "APP_PACKAGES",
    "SYSTEM_PROMPT",
    "SYSTEM_PROMPT_RU",
    "SYSTEM_PROMPT_EN",
    "get_system_prompt",
    "get_messages",
    "get_message",
]
