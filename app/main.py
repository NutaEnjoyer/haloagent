"""
Main FastAPI application for Voice Caller API.
"""
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes_call, routes_telephony, routes_demo, routes_voximplant, routes_websocket
from app.config import settings
from app.core.orchestrator import CallOrchestrator
from app.integrations.google_sheets import GoogleSheetsClient
from app.integrations.openai_client import OpenAIClient
from app.integrations.telephony_stub import StubTelephonyAdapter
from app.integrations.telephony_voximplant import VoximplantTelephonyAdapter
from app.utils.logging import logger

# Global instances
_orchestrator: CallOrchestrator = None
_telephony_adapter = None
_openai_client: OpenAIClient = None


def get_orchestrator() -> CallOrchestrator:
    """
    Get the global orchestrator instance.

    Returns:
        CallOrchestrator instance
    """
    global _orchestrator
    if _orchestrator is None:
        raise RuntimeError("Orchestrator not initialized")
    return _orchestrator


def get_telephony_adapter():
    """
    Get the global telephony adapter instance.

    Returns:
        Telephony adapter instance
    """
    global _telephony_adapter
    if _telephony_adapter is None:
        raise RuntimeError("Telephony adapter not initialized")
    return _telephony_adapter


def get_openai_client() -> OpenAIClient:
    """
    Get the global OpenAI client instance.

    Returns:
        OpenAI client instance
    """
    global _openai_client
    if _openai_client is None:
        raise RuntimeError("OpenAI client not initialized")
    return _openai_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown.

    Args:
        app: FastAPI application instance
    """
    global _orchestrator, _telephony_adapter, _openai_client

    # Startup
    logger.info("Starting Voice Caller API...")

    try:
        # Initialize clients
        logger.info("Initializing OpenAI client...")
        openai_client = OpenAIClient()
        _openai_client = openai_client  # Store globally

        # Initialize Google Sheets client (real or mock)
        if settings.USE_MOCK_SHEETS:
            logger.info("Initializing Google Sheets client (MOCK mode)...")
            from app.integrations.google_sheets_mock import MockGoogleSheetsClient
            sheets_client = MockGoogleSheetsClient()
        else:
            logger.info("Initializing Google Sheets client...")
            from app.integrations.google_sheets import GoogleSheetsClient
            sheets_client = GoogleSheetsClient()

        # Event callback for telephony events
        async def telephony_event_callback(call_id: str, event, reason):
            """Callback for telephony events."""
            await _orchestrator.handle_telephony_event(call_id, event, reason)

        # Initialize Telephony adapter (Voximplant or Stub)
        if settings.USE_VOXIMPLANT:
            logger.info("Initializing Telephony adapter (Voximplant mode)...")

            # Validate Voximplant configuration
            if not all([
                settings.VOXIMPLANT_ACCOUNT_ID,
                settings.VOXIMPLANT_API_KEY,
                settings.VOXIMPLANT_APPLICATION_ID,
                settings.VOXIMPLANT_RULE_ID,
                settings.BACKEND_URL
            ]):
                raise ValueError(
                    "Voximplant configuration incomplete. Required: "
                    "VOXIMPLANT_ACCOUNT_ID, VOXIMPLANT_API_KEY, "
                    "VOXIMPLANT_APPLICATION_ID, VOXIMPLANT_RULE_ID, BACKEND_URL"
                )

            telephony_adapter = VoximplantTelephonyAdapter(
                account_id=settings.VOXIMPLANT_ACCOUNT_ID,
                api_key=settings.VOXIMPLANT_API_KEY,
                application_id=settings.VOXIMPLANT_APPLICATION_ID,
                rule_id=settings.VOXIMPLANT_RULE_ID,
                caller_id=settings.VOXIMPLANT_CALLER_ID,
                backend_url=settings.BACKEND_URL,
                event_callback=telephony_event_callback
            )

            logger.info(
                f"Voximplant adapter initialized | "
                f"account_id={settings.VOXIMPLANT_ACCOUNT_ID} | "
                f"webhook_url={settings.BACKEND_URL}/voximplant/events"
            )

        else:
            logger.info("Initializing Telephony adapter (Stub mode)...")
            telephony_adapter = StubTelephonyAdapter(event_callback=telephony_event_callback)

        # Store telephony adapter globally
        _telephony_adapter = telephony_adapter

        # Initialize orchestrator
        logger.info("Initializing Call Orchestrator...")
        _orchestrator = CallOrchestrator(
            telephony_adapter=telephony_adapter,
            openai_client=openai_client,
            sheets_client=sheets_client
        )

        logger.info("Voice Caller API started successfully")

    except Exception as e:
        logger.error(f"Failed to start application: {e}", exc_info=True)
        raise

    yield

    # Shutdown
    logger.info("Shutting down Voice Caller API...")
    # Add cleanup if needed


# Create FastAPI app
app = FastAPI(
    title="Voice Caller API",
    description="MVP сервиса голосового обзвона с использованием OpenAI",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(routes_call.router, tags=["calls"])
app.include_router(routes_telephony.router, tags=["telephony"])
app.include_router(routes_demo.router)  # Demo cabinet routes
app.include_router(routes_voximplant.router)  # Voximplant webhooks
app.include_router(routes_websocket.router)  # WebSocket streaming


@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        Health status and basic metrics
    """
    active_calls = len(_orchestrator.active_calls) if _orchestrator else 0

    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "active_calls": active_calls,
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """
    Root endpoint.

    Returns:
        Welcome message
    """
    return {
        "service": "Voice Caller API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
