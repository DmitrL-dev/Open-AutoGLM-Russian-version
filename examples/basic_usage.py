#!/usr/bin/env python3
"""
Phone Agent Usage Examples

Demonstrates how to use Phone Agent for phone automation tasks via Python API.
"""

from phone_agent import PhoneAgent
from phone_agent.agent import AgentConfig
from phone_agent.config import get_messages
from phone_agent.model import ModelConfig


def example_basic_task(lang: str = "en"):
    """Basic task example."""
    msgs = get_messages(lang)

    # Configure model endpoint
    model_config = ModelConfig(
        base_url="http://localhost:8000/v1",
        model_name="autoglm-phone-9b",
        temperature=0.1,
    )

    # Configure Agent behavior
    agent_config = AgentConfig(
        max_steps=50,
        verbose=True,
        lang=lang,
    )

    # Create Agent
    agent = PhoneAgent(
        model_config=model_config,
        agent_config=agent_config,
    )

    # Execute task
    result = agent.run("Open Chrome and search for weather")
    print(f"{msgs['task_result']}: {result}")


def example_with_callbacks(lang: str = "en"):
    """Task example with callbacks."""
    msgs = get_messages(lang)

    def my_confirmation(message: str) -> bool:
        """Sensitive operation confirmation callback."""
        print(f"\n[{msgs['confirmation_required']}] {message}")
        response = input(f"{msgs['continue_prompt']}: ")
        return response.lower() in ("yes", "y")

    def my_takeover(message: str) -> None:
        """Manual takeover callback."""
        print(f"\n[{msgs['manual_operation_required']}] {message}")
        print(msgs["manual_operation_hint"])
        input(f"{msgs['press_enter_when_done']}: ")

    # Create Agent with custom callbacks
    agent_config = AgentConfig(lang=lang)
    agent = PhoneAgent(
        agent_config=agent_config,
        confirmation_callback=my_confirmation,
        takeover_callback=my_takeover,
    )

    # Execute task that may require confirmation
    result = agent.run("Open Google Play Store and search for Telegram")
    print(f"{msgs['task_result']}: {result}")


def example_step_by_step(lang: str = "en"):
    """Step-by-step execution example (for debugging)."""
    msgs = get_messages(lang)

    agent_config = AgentConfig(lang=lang)
    agent = PhoneAgent(agent_config=agent_config)

    # Initialize task
    result = agent.step("Open Settings and check WiFi status")
    print(f"{msgs['step']} 1: {result.action}")

    # Continue if not finished
    while not result.finished and agent.step_count < 10:
        result = agent.step()
        print(f"{msgs['step']} {agent.step_count}: {result.action}")
        print(f"  {msgs['thinking']}: {result.thinking[:100]}...")

    print(f"\n{msgs['final_result']}: {result.message}")


def example_multiple_tasks(lang: str = "en"):
    """Batch task example."""
    msgs = get_messages(lang)

    agent_config = AgentConfig(lang=lang)
    agent = PhoneAgent(agent_config=agent_config)

    tasks = [
        "Open Google Maps and check traffic",
        "Open Chrome and search for news",
        "Open Settings and check battery level",
    ]

    for task in tasks:
        print(f"\n{'=' * 50}")
        print(f"{msgs['task']}: {task}")
        print("=" * 50)

        result = agent.run(task)
        print(f"{msgs['result']}: {result}")

        # Reset Agent state
        agent.reset()


def example_remote_device(lang: str = "en"):
    """Remote device example."""
    from phone_agent.adb import ADBConnection

    msgs = get_messages(lang)

    # Create connection manager
    conn = ADBConnection()

    # Connect to remote device
    success, message = conn.connect("192.168.1.100:5555")
    if not success:
        print(f"{msgs['connection_failed']}: {message}")
        return

    print(f"{msgs['connection_successful']}: {message}")

    # Create Agent with device specified
    agent_config = AgentConfig(
        device_id="192.168.1.100:5555",
        verbose=True,
        lang=lang,
    )

    agent = PhoneAgent(agent_config=agent_config)

    # Execute task
    result = agent.run("Open Telegram and check messages")
    print(f"{msgs['task_result']}: {result}")

    # Disconnect
    conn.disconnect("192.168.1.100:5555")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Phone Agent Usage Examples")
    parser.add_argument(
        "--lang",
        type=str,
        default="en",
        choices=["ru", "en"],
        help="Language for UI messages (ru=Russian, en=English)",
    )
    args = parser.parse_args()

    print("Phone Agent Usage Examples")
    print("=" * 50)

    # Run basic example
    print("\n1. Basic Task Example")
    print("-" * 30)
    example_basic_task(args.lang)

    # Uncomment to run other examples
    # print("\n2. Task Example with Callbacks")
    # print("-" * 30)
    # example_with_callbacks(args.lang)

    # print("\n3. Step-by-step Example")
    # print("-" * 30)
    # example_step_by_step(args.lang)

    # print("\n4. Batch Task Example")
    # print("-" * 30)
    # example_multiple_tasks(args.lang)

    # print("\n5. Remote Device Example")
    # print("-" * 30)
    # example_remote_device(args.lang)
