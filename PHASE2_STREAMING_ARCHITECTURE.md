# Phase 2 - Streaming Architecture

## Overview

Phase 2 implements **real-time bidirectional audio streaming** for voice calls using:
- **Voximplant** (telephony provider)
- **OpenAI Realtime API** (STT + GPT + TTS in one WebSocket connection)
- **WebSocket** bidirectional communication

## Architecture Diagram

```
┌─────────────────┐
│   Voximplant    │
│   VoxEngine     │
│  (PSTN call)    │
└────────┬────────┘
         │ WebSocket
         │ /ws/audio/{call_id}
         ↓
┌─────────────────────────────────────────────────────┐
│              Backend (FastAPI)                      │
│                                                     │
│  ┌────────────────────────────────────────────┐   │
│  │  routes_websocket.py                       │   │
│  │  - Receives audio from Voximplant          │   │
│  │  - Forwards to OpenAI Realtime client      │   │
│  │  - Sends assistant audio back to Voximplant│   │
│  └───────────┬────────────────────────────────┘   │
│              │                                      │
│              │ Forward audio                        │
│              ↓                                      │
│  ┌────────────────────────────────────────────┐   │
│  │  streaming_dialog_manager.py               │   │
│  │  - Manages OpenAI Realtime client          │   │
│  │  - Registers client with WebSocket         │   │
│  │  - Processes OpenAI events                 │   │
│  │  - Saves transcripts to CallSession        │   │
│  └───────────┬────────────────────────────────┘   │
│              │                                      │
│              │ WebSocket                            │
│              ↓                                      │
└──────────────┼──────────────────────────────────────┘
               │
               │ wss://api.openai.com/v1/realtime
               ↓
      ┌────────────────────┐
      │  OpenAI Realtime   │
      │  API               │
      │  - STT (Whisper)   │
      │  - GPT-4o          │
      │  - TTS (voice)     │
      └────────────────────┘
```

## Data Flow

### 1. Voximplant → OpenAI (User Speech)

```
User speaks
  ↓
Voximplant VoxEngine captures audio (PCM16, 24kHz, mono)
  ↓
VoxEngine sends via WebSocket to /ws/audio/{call_id}
  ↓
routes_websocket.py receives audio bytes
  ↓
routes_websocket.py forwards to registered OpenAI client
  ↓
OpenAI Realtime API processes:
  - STT: converts speech to text
  - GPT: generates response
  - TTS: converts response to audio
```

### 2. OpenAI → Voximplant (Assistant Response)

```
OpenAI generates TTS audio chunks
  ↓
streaming_dialog_manager receives via receive_events()
  ↓
streaming_dialog_manager calls routes_websocket.send_audio_to_voximplant()
  ↓
routes_websocket.py sends audio bytes via WebSocket
  ↓
Voximplant VoxEngine receives audio
  ↓
VoxEngine plays audio to user
```

## Key Components

### 1. `app/integrations/openai_realtime.py`

**OpenAI Realtime API client**

- Connects to OpenAI via WebSocket
- Sends audio chunks with `send_audio_chunk(audio_bytes)`
- Receives events via async generator `receive_events()`
- Event types:
  - `audio_delta` - TTS audio chunk
  - `user_transcript` - STT result (user spoke)
  - `assistant_transcript_delta` - Assistant speaking
  - `turn_complete` - Turn finished
  - `error` - Error occurred

**Configuration:**
```python
realtime_client = OpenAIRealtimeClient(api_key=openai_api_key)
await realtime_client.connect(
    voice="alloy",           # TTS voice
    instructions="...",      # System prompt
    temperature=0.8,
    input_audio_format="pcm16",
    output_audio_format="pcm16"
)
```

### 2. `app/core/streaming_dialog_manager.py`

**Streaming Dialog Manager**

- Creates and manages OpenAI Realtime client
- Registers client with WebSocket endpoint
- Processes OpenAI events
- Saves transcripts to `CallSession`
- Forwards assistant audio to Voximplant

**Key methods:**
```python
async def run_streaming_dialog(
    call_id: str,
    call_session: CallSession,
    voice: str,       # TTS voice
    language: str,    # Language code
    prompt: str       # Custom instructions
)
```

### 3. `app/api/routes_websocket.py`

**WebSocket endpoint for audio streaming**

- Endpoint: `/ws/audio/{call_id}`
- Accepts WebSocket connections from Voximplant VoxEngine
- Maintains registry of OpenAI clients per call_id
- Forwards audio bidirectionally

**Global registries:**
```python
active_connections: Dict[str, WebSocket] = {}          # Voximplant connections
openai_clients: Dict[str, OpenAIRealtimeClient] = {}   # OpenAI clients
```

**Helper functions:**
```python
register_openai_client(call_id, client)      # Register OpenAI client
unregister_openai_client(call_id)            # Cleanup
send_audio_to_voximplant(call_id, audio)     # Send to Voximplant
is_websocket_connected(call_id)              # Check connection
```

### 4. `app/core/orchestrator.py`

**Automatic mode selection**

The orchestrator automatically chooses between streaming and regular dialog:

```python
async def _run_dialog_and_finalize(self, call_id: str):
    # Check if streaming settings are present
    use_streaming = (
        call_session.demo_voice is not None or
        call_session.demo_language is not None or
        call_session.demo_prompt is not None
    )

    if use_streaming:
        # Use Streaming Dialog Manager (Phase 2)
        await self.streaming_dialog_manager.run_streaming_dialog(...)
    else:
        # Use regular Dialog Manager (Phase 1)
        await self.dialog_manager.run_dialog(...)
```

### 5. VoxEngine Scenario (`VOXENGINE_SCENARIO_PHASE2.js`)

**Voximplant side implementation**

- Initiates PSTN call
- Connects to backend WebSocket: `wss://your-backend.com/ws/audio/{call_id}`
- Captures user audio using `VoxEngine.createRecorder()`
- Sends audio chunks to backend
- Receives assistant audio from backend
- Plays audio to user via `callSession.sendAudio()`

**Audio format:**
- Format: PCM16
- Channels: Mono (1)
- Sample rate: 24kHz

## Demo Session Integration

When creating a demo session via `/demo/sessions`:

```python
# Frontend sends:
{
    "phone": "+79991234567",
    "voice": "alloy",        # OpenAI voice
    "language": "ru",        # Language code
    "prompt": "Вы - ассистент компании HALO..."
}

# Backend creates CallSession with demo settings:
call_session.demo_voice = "alloy"
call_session.demo_language = "ru"
call_session.demo_prompt = "Вы - ассистент..."

# Orchestrator detects settings and uses streaming mode
```

## Supported Languages

OpenAI Realtime API auto-detects language, but you can specify:

- `auto` - Auto-detect
- `ru` - Russian
- `uz` - Uzbek
- `tj` - Tajik
- `kk` - Kazakh
- `ky` - Kyrgyz
- `tm` - Turkmen
- `az` - Azerbaijani
- `fa-af` - Dari (Afghan Persian)
- `en` - English
- `tr` - Turkish

Instructions are automatically adjusted based on selected language.

## Supported Voices

OpenAI TTS voices:
- `alloy` - Neutral
- `echo` - Male
- `fable` - Female (British accent)
- `onyx` - Male (deep)
- `nova` - Female (energetic)
- `shimmer` - Female (soft)

## Error Handling

### WebSocket Disconnection

If Voximplant disconnects:
- `routes_websocket.py` removes connection from `active_connections`
- OpenAI client remains registered
- Streaming loop continues processing OpenAI events
- When OpenAI connection closes, cleanup happens in `finally` block

### OpenAI Error

If OpenAI returns error event:
```python
elif event_type == "error":
    logger.error(f"OpenAI error: {data}")
    break  # Exit streaming loop
```

Call is marked as FAILED and finalized.

### No WebSocket Connection

If streaming dialog starts but Voximplant hasn't connected yet:
- OpenAI client is registered
- WebSocket endpoint logs warning when receiving audio without client
- Assistant audio is buffered (or dropped if connection never establishes)

## Testing Checklist

- [ ] Start backend with `docker-compose up`
- [ ] Verify `.env` has correct Voximplant credentials
- [ ] Create demo session via frontend form
- [ ] Check logs for:
  - `[Voximplant] Call initiated successfully`
  - `[WebSocket] Audio stream connected`
  - `[OpenAI Realtime] Connected successfully`
  - `[Streaming Dialog] Audio forwarding started`
- [ ] Verify bidirectional audio flow:
  - User speaks → WebSocket receives audio → OpenAI processes → transcript logged
  - OpenAI responds → audio sent to Voximplant → user hears response
- [ ] Check transcript in CallSession after call ends
- [ ] Verify call is properly finalized and saved to Google Sheets

## Troubleshooting

### No audio from user

**Check:**
1. VoxEngine recorder is started
2. WebSocket connection is established
3. OpenAI client is registered in `openai_clients`
4. Audio format is PCM16, 24kHz, mono

### No audio from assistant

**Check:**
1. OpenAI Realtime API is connected
2. `send_audio_to_voximplant()` is being called
3. WebSocket connection to Voximplant is active
4. Voximplant is receiving audio bytes

### Transcripts not saved

**Check:**
1. `on_transcript_delta` handler is set
2. Events `user_transcript` and `assistant_transcript_delta` are received
3. `call_session.add_turn()` is called

### High latency

**Optimize:**
1. Use smaller audio chunks (50-100ms)
2. Ensure backend has good connection to OpenAI
3. Check Voximplant server location (use closest region)
4. Reduce GPT temperature for faster responses

## Next Steps (Phase 3)

After streaming is working:
1. Implement post-call follow-up generation via GPT
2. Add SMS provider for deep-link
3. Create Telegram bot for chat continuation
4. Extract interest level from transcript
5. Create real CRM records
