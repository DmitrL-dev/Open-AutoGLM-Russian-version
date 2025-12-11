"""REST API server for Phone Agent.

Provides HTTP endpoints to control the agent remotely.
Security features:
- Localhost binding by default
- API key authentication
- Rate limiting
- Action whitelist
"""

import asyncio
import time
from contextlib import asynccontextmanager
from datetime import datetime
from functools import wraps
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from phone_agent.models import (
    APIConfig,
    ModelConfigPydantic,
    AgentConfigPydantic,
    ActionType,
    ActionRequest,
    Language,
)
from phone_agent.device_state import check_device_state, DeviceState
from phone_agent.ui_tree import get_ui_tree, UIElement
from phone_agent.utils import logger


# Rate limiting storage
rate_limit_store: dict[str, list[float]] = {}


class TaskRequest(BaseModel):
    """Request to execute a task."""

    task: str = Field(description="Natural language task description")
    lang: Language = Field(default=Language.ENGLISH)
    max_steps: int = Field(default=50, ge=1, le=200)


class ActionExecuteRequest(BaseModel):
    """Request to execute a single action."""

    action: ActionRequest


class StatusResponse(BaseModel):
    """API status response."""

    status: str
    version: str
    device_connected: bool
    device_ready: bool
    timestamp: str


class TaskResponse(BaseModel):
    """Task execution response."""

    success: bool
    message: str
    steps_executed: int
    duration_seconds: float


class ElementInfo(BaseModel):
    """UI element information."""

    text: str
    resource_id: str
    class_name: str
    bounds: tuple[int, int, int, int]
    center: tuple[int, int]
    clickable: bool


def create_api(config: Optional[APIConfig] = None) -> FastAPI:
    """
    Create configured FastAPI application.

    Args:
        config: API configuration. Uses defaults if None.

    Returns:
        Configured FastAPI app.
    """
    config = config or APIConfig()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info(f"Starting Phone Agent API on {config.host}:{config.port}")
        yield
        logger.info("Shutting down Phone Agent API")

    app = FastAPI(
        title="Phone Agent API",
        description="REST API for AI-powered Android automation",
        version="0.2.0",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    # Store config in app state
    app.state.config = config
    app.state.agent = None  # Lazy initialization

    # Auth dependency
    async def verify_api_key(x_api_key: Optional[str] = Header(None)):
        if config.api_key and x_api_key != config.api_key:
            raise HTTPException(status_code=401, detail="Invalid API key")
        return True

    # Rate limiting dependency
    async def check_rate_limit(request: Request):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Clean old entries
        if client_ip in rate_limit_store:
            rate_limit_store[client_ip] = [
                t for t in rate_limit_store[client_ip] if now - t < 60
            ]
        else:
            rate_limit_store[client_ip] = []

        # Check limit
        if len(rate_limit_store[client_ip]) >= config.rate_limit:
            raise HTTPException(
                status_code=429, detail=f"Rate limit exceeded ({config.rate_limit}/min)"
            )

        rate_limit_store[client_ip].append(now)
        return True

    @app.get("/", response_model=StatusResponse)
    async def get_status():
        """Get API and device status."""
        try:
            state = check_device_state()
            device_connected = state.is_connected
            device_ready = state.is_ready
        except Exception:
            device_connected = False
            device_ready = False

        return StatusResponse(
            status="ok",
            version="0.2.0",
            device_connected=device_connected,
            device_ready=device_ready,
            timestamp=datetime.now().isoformat(),
        )

    @app.get("/device", dependencies=[Depends(verify_api_key)])
    async def get_device_state():
        """Get detailed device state."""
        try:
            state = check_device_state()
            return {
                "connected": state.is_connected,
                "ready": state.is_ready,
                "screen": state.screen_state.value,
                "lock": state.lock_state.value,
                "battery": state.battery_level,
                "current_app": state.current_app,
                "issues": state.get_issues(),
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/ui/tree", dependencies=[Depends(verify_api_key)])
    async def get_ui_elements():
        """Get current UI tree elements."""
        try:
            tree = get_ui_tree()
            clickable = tree.get_clickable_elements()

            return {
                "total_elements": len(clickable),
                "elements": [
                    ElementInfo(
                        text=el.display_text,
                        resource_id=el.resource_id,
                        class_name=el.class_name,
                        bounds=el.bounds,
                        center=el.center,
                        clickable=el.clickable,
                    ).model_dump()
                    for el in clickable[:50]  # Limit to 50
                ],
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post(
        "/task",
        response_model=TaskResponse,
        dependencies=[Depends(verify_api_key), Depends(check_rate_limit)],
    )
    async def execute_task(request: TaskRequest):
        """Execute a natural language task."""
        from phone_agent import PhoneAgent
        from phone_agent.agent import AgentConfig
        from phone_agent.model import ModelConfig

        start_time = time.time()

        try:
            # Create agent (could cache this)
            agent_config = AgentConfig(
                max_steps=request.max_steps,
                lang=request.lang.value,
            )
            agent = PhoneAgent(agent_config=agent_config)

            # Run task in thread pool (blocking call)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, agent.run, request.task)

            return TaskResponse(
                success=True,
                message=result,
                steps_executed=agent.step_count,
                duration_seconds=time.time() - start_time,
            )
        except Exception as e:
            logger.error(f"Task failed: {e}")
            return TaskResponse(
                success=False,
                message=str(e),
                steps_executed=0,
                duration_seconds=time.time() - start_time,
            )

    @app.post(
        "/action", dependencies=[Depends(verify_api_key), Depends(check_rate_limit)]
    )
    async def execute_action(request: ActionExecuteRequest):
        """Execute a single action directly."""
        from phone_agent.actions import ActionHandler

        # Check whitelist
        if request.action.action not in config.allowed_actions:
            raise HTTPException(
                status_code=403,
                detail=f"Action '{request.action.action.value}' not allowed",
            )

        try:
            handler = ActionHandler()
            action_dict = request.action.to_dict()

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, handler.execute, action_dict)

            return {"success": True, "result": result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/actions/allowed")
    async def get_allowed_actions():
        """Get list of allowed actions."""
        return {"actions": [a.value for a in config.allowed_actions]}

    return app


def run_api(
    host: str = "127.0.0.1",
    port: int = 8080,
    api_key: Optional[str] = None,
    reload: bool = False,
):
    """
    Run the API server.

    Args:
        host: Host to bind (default: localhost only).
        port: Port to listen on.
        api_key: Optional API key for auth.
        reload: Enable auto-reload for development.
    """
    import uvicorn

    config = APIConfig(host=host, port=port, api_key=api_key)
    app = create_api(config)

    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Phone Agent API Server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--reload", action="store_true")

    args = parser.parse_args()
    run_api(args.host, args.port, args.api_key, args.reload)
