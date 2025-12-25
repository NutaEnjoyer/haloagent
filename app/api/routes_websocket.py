"""
WebSocket routes for streaming audio.

Provides WebSocket endpoints for real-time audio streaming between
Voximplant and backend.
"""
import asyncio
from typing import Dict, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

from app.integrations.openai_realtime import OpenAIRealtimeClient
from app.utils.logging import logger

router = APIRouter(prefix="/ws", tags=["websocket"])

# Active WebSocket connections per call
active_connections: Dict[str, WebSocket] = {}

# Active OpenAI Realtime clients per call (set by StreamingDialogManager)
openai_clients: Dict[str, OpenAIRealtimeClient] = {}


@router.websocket("/audio/{call_id}")
async def audio_stream(websocket: WebSocket, call_id: str):
    """
    WebSocket endpoint for bidirectional audio streaming.

    Voximplant VoxEngine connects here to:
    - Send user audio to backend
    - Receive assistant audio from backend

    Args:
        websocket: WebSocket connection
        call_id: Call identifier
    """
    try:
        # Accept connection
        await websocket.accept()
        active_connections[call_id] = websocket

        logger.info(f"[WebSocket] Audio stream connected | call_id={call_id}")

        # Send initial handshake
        await websocket.send_json({
            "type": "connected",
            "call_id": call_id,
            "message": "Audio stream ready"
        })

        # Keep connection alive and handle audio
        while True:
            try:
                # Receive audio chunk from Voximplant
                data = await websocket.receive()

                if "bytes" in data:
                    # Binary audio data
                    audio_bytes = data["bytes"]

                    logger.debug(
                        f"[WebSocket] Received audio | "
                        f"call_id={call_id} | size={len(audio_bytes)} bytes"
                    )

                    # Forward to OpenAI Realtime API if client is registered
                    openai_client = openai_clients.get(call_id)
                    if openai_client and openai_client.connected:
                        await openai_client.send_audio_chunk(audio_bytes)
                    else:
                        logger.warning(
                            f"[WebSocket] No OpenAI client registered for call_id={call_id}"
                        )

                elif "text" in data:
                    # Text message (control messages)
                    import json
                    message = json.loads(data["text"])
                    msg_type = message.get("type")

                    logger.debug(f"[WebSocket] Received message | call_id={call_id} | type={msg_type}")

                    if msg_type == "ping":
                        # Respond to ping
                        await websocket.send_json({"type": "pong"})

                    elif msg_type == "close":
                        # Voximplant requests close
                        logger.info(f"[WebSocket] Close requested | call_id={call_id}")
                        break

            except WebSocketDisconnect:
                logger.info(f"[WebSocket] Client disconnected | call_id={call_id}")
                break

            except Exception as e:
                logger.error(
                    f"[WebSocket] Error receiving data | call_id={call_id} | error={e}",
                    exc_info=True
                )
                break

    except Exception as e:
        logger.error(
            f"[WebSocket] Connection error | call_id={call_id} | error={e}",
            exc_info=True
        )

    finally:
        # Cleanup
        if call_id in active_connections:
            del active_connections[call_id]

        # Note: Don't delete openai_clients here - StreamingDialogManager manages that

        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.close()

        logger.info(f"[WebSocket] Audio stream closed | call_id={call_id}")


async def send_audio_to_voximplant(call_id: str, audio_bytes: bytes) -> bool:
    """
    Send audio chunk to Voximplant via WebSocket.

    Args:
        call_id: Call identifier
        audio_bytes: Audio data to send

    Returns:
        True if sent successfully, False otherwise
    """
    ws = active_connections.get(call_id)

    if not ws:
        logger.warning(f"[WebSocket] No active connection for call_id={call_id}")
        return False

    try:
        if ws.client_state == WebSocketState.CONNECTED:
            await ws.send_bytes(audio_bytes)
            return True
        else:
            logger.warning(
                f"[WebSocket] Connection not in CONNECTED state | call_id={call_id}"
            )
            return False

    except Exception as e:
        logger.error(
            f"[WebSocket] Error sending audio | call_id={call_id} | error={e}",
            exc_info=True
        )
        return False


def is_websocket_connected(call_id: str) -> bool:
    """
    Check if WebSocket is connected for a call.

    Args:
        call_id: Call identifier

    Returns:
        True if connected, False otherwise
    """
    ws = active_connections.get(call_id)
    return ws is not None and ws.client_state == WebSocketState.CONNECTED


def register_openai_client(call_id: str, client: OpenAIRealtimeClient) -> None:
    """
    Register OpenAI Realtime client for a call.

    This allows the WebSocket endpoint to forward audio to the client.

    Args:
        call_id: Call identifier
        client: OpenAI Realtime client instance
    """
    openai_clients[call_id] = client
    logger.info(f"[WebSocket] OpenAI client registered | call_id={call_id}")


def unregister_openai_client(call_id: str) -> None:
    """
    Unregister OpenAI Realtime client for a call.

    Args:
        call_id: Call identifier
    """
    if call_id in openai_clients:
        del openai_clients[call_id]
        logger.info(f"[WebSocket] OpenAI client unregistered | call_id={call_id}")
