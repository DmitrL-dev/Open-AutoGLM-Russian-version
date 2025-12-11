"""Internationalization (i18n) module for Phone Agent UI messages."""

# Russian messages
MESSAGES_RU = {
    "thinking": "Размышление",
    "action": "Действие",
    "task_completed": "Задача выполнена",
    "done": "Готово",
    "starting_task": "Начинаю выполнение задачи",
    "final_result": "Итоговый результат",
    "task_result": "Результат задачи",
    "confirmation_required": "Требуется подтверждение",
    "continue_prompt": "Продолжить? (y/n)",
    "manual_operation_required": "Требуется ручное управление",
    "manual_operation_hint": "Пожалуйста, выполните операцию вручную...",
    "press_enter_when_done": "Нажмите Enter после завершения",
    "connection_failed": "Ошибка подключения",
    "connection_successful": "Подключение успешно",
    "step": "Шаг",
    "task": "Задача",
    "result": "Результат",
}

# English messages
MESSAGES_EN = {
    "thinking": "Thinking",
    "action": "Action",
    "task_completed": "Task Completed",
    "done": "Done",
    "starting_task": "Starting task",
    "final_result": "Final Result",
    "task_result": "Task Result",
    "confirmation_required": "Confirmation Required",
    "continue_prompt": "Continue? (y/n)",
    "manual_operation_required": "Manual Operation Required",
    "manual_operation_hint": "Please complete the operation manually...",
    "press_enter_when_done": "Press Enter when done",
    "connection_failed": "Connection Failed",
    "connection_successful": "Connection Successful",
    "step": "Step",
    "task": "Task",
    "result": "Result",
}


def get_messages(lang: str = "en") -> dict:
    """
    Get UI messages dictionary by language.

    Args:
        lang: Language code, 'ru' for Russian, 'en' for English.

    Returns:
        Dictionary of UI messages.
    """
    if lang == "ru":
        return MESSAGES_RU
    return MESSAGES_EN


def get_message(key: str, lang: str = "en") -> str:
    """
    Get a single UI message by key and language.

    Args:
        key: Message key.
        lang: Language code, 'ru' for Russian, 'en' for English.

    Returns:
        Message string.
    """
    messages = get_messages(lang)
    return messages.get(key, key)
