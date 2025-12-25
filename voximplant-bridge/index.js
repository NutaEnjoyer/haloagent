/**
 * Voximplant Bridge Server
 *
 * Connects Backend to VoxEngine calls using Voximplant Web SDK
 *
 * Architecture:
 * 1. Backend calls POST /connect with call_id when call is answered
 * 2. Bridge connects to VoxEngine using Web SDK
 * 3. VoxEngine uses sendMediaBetween() to bridge PSTN <-> Backend
 * 4. Audio flows: User <-> VoxEngine <-> Bridge <-> Backend <-> OpenAI
 */

const express = require('express');
const VoxImplant = require('voximplant-websdk');
const WebSocket = require('ws');

const app = express();
const PORT = 3000;

// Voximplant credentials
const VOXIMPLANT_USER = 'firstuser@halodemo.ginai-acc.n3.voximplant.com';
const VOXIMPLANT_PASSWORD = '6S[3rz0X';

// Backend WebSocket endpoint (host machine)
const BACKEND_WS_URL = 'ws://host.docker.internal:8000';

const sdk = VoxImplant.getInstance();
const activeCalls = new Map(); // call_id -> {call, ws}

// Initialize Voximplant SDK
async function initSDK() {
    console.log('[Bridge] Initializing Voximplant SDK...');

    try {
        await sdk.init({
            micRequired: true,
            videoSupport: false
        });

        await sdk.connect();
        console.log('[Bridge] ✓ Connected to Voximplant platform');

        await sdk.login(VOXIMPLANT_USER, VOXIMPLANT_PASSWORD);
        console.log('[Bridge] ✓ Logged in as', VOXIMPLANT_USER);

        return true;
    } catch (error) {
        console.error('[Bridge] SDK initialization error:', error);
        throw error;
    }
}

// Connect to VoxEngine call
async function connectToCall(callId) {
    console.log(`[Bridge] Connecting to VoxEngine call: ${callId}`);

    try {
        // Make call to VoxEngine using call_id as number
        // VoxEngine listens for this via AppEvents.CallAlerting
        const call = sdk.call({
            number: callId,
            video: false,
            customData: JSON.stringify({ call_id: callId })
        });

        // Track call events
        call.addEventListener(VoxImplant.CallEvents.Connected, () => {
            console.log(`[Bridge] ✓ Connected to VoxEngine | call_id=${callId}`);
            console.log(`[Bridge] Audio bridge now active - VoxEngine will use sendMediaBetween()`);

            // Now connect to Backend WebSocket for OpenAI streaming
            connectToBackend(callId, call);
        });

        call.addEventListener(VoxImplant.CallEvents.Disconnected, () => {
            console.log(`[Bridge] Disconnected from VoxEngine | call_id=${callId}`);
            cleanup(callId);
        });

        call.addEventListener(VoxImplant.CallEvents.Failed, (e) => {
            console.error(`[Bridge] VoxEngine call failed | call_id=${callId}:`, e);
            cleanup(callId);
        });

        // Store call reference
        if (!activeCalls.has(callId)) {
            activeCalls.set(callId, {});
        }
        activeCalls.get(callId).call = call;

        return { status: 'connecting', call_id: callId };

    } catch (error) {
        console.error(`[Bridge] Connection error for ${callId}:`, error);
        throw error;
    }
}

// Connect to Backend WebSocket for OpenAI Realtime streaming
function connectToBackend(callId, voxCall) {
    console.log(`[Bridge] Connecting to Backend WebSocket | call_id=${callId}`);

    const wsUrl = `${BACKEND_WS_URL}/ws/audio/${callId}`;
    const ws = new WebSocket(wsUrl);

    ws.on('open', () => {
        console.log(`[Bridge] ✓ Connected to Backend WebSocket | call_id=${callId}`);
        console.log(`[Bridge] Full audio path established: User <-> VoxEngine <-> Bridge <-> Backend <-> OpenAI`);
    });

    ws.on('message', (data) => {
        // Backend sends audio from OpenAI to play to user
        // This audio should be sent to Voximplant call
        // TODO: Implement audio streaming from Backend to Voximplant
        console.log(`[Bridge] <- Backend audio: ${data.length} bytes | call_id=${callId}`);
    });

    ws.on('close', () => {
        console.log(`[Bridge] Backend WebSocket closed | call_id=${callId}`);
        // If Backend disconnects, hang up VoxEngine call
        if (voxCall) {
            voxCall.hangup();
        }
        cleanup(callId);
    });

    ws.on('error', (err) => {
        console.error(`[Bridge] Backend WebSocket error | call_id=${callId}:`, err);
    });

    // Store WebSocket reference
    if (activeCalls.has(callId)) {
        activeCalls.get(callId).ws = ws;
    }
}

// Cleanup call resources
function cleanup(callId) {
    console.log(`[Bridge] Cleaning up call resources | call_id=${callId}`);

    const callData = activeCalls.get(callId);
    if (callData) {
        if (callData.ws) {
            try {
                callData.ws.close();
            } catch (e) {
                console.error(`[Bridge] Error closing WebSocket:`, e);
            }
        }
        activeCalls.delete(callId);
    }
}

// REST API
app.use(express.json());

// Health check
app.get('/health', (req, res) => {
    const clientState = sdk.getClientState();
    res.json({
        status: 'ok',
        logged_in: clientState === VoxImplant.ClientState.LOGGED_IN,
        active_calls: activeCalls.size
    });
});

// Connect to a call
app.post('/connect', async (req, res) => {
    const { call_id } = req.body;

    if (!call_id) {
        return res.status(400).json({ error: 'call_id required' });
    }

    console.log(`[Bridge] Received connect request | call_id=${call_id}`);

    try {
        const result = await connectToCall(call_id);
        res.json(result);
    } catch (error) {
        console.error(`[Bridge] Connect error:`, error);
        res.status(500).json({ error: error.message });
    }
});

// Disconnect a call
app.post('/disconnect', async (req, res) => {
    const { call_id } = req.body;

    if (!call_id) {
        return res.status(400).json({ error: 'call_id required' });
    }

    const callData = activeCalls.get(call_id);
    if (callData && callData.call) {
        callData.call.hangup();
        cleanup(call_id);
        res.json({ status: 'disconnected', call_id });
    } else {
        res.status(404).json({ error: 'Call not found' });
    }
});

// Get status
app.get('/status', (req, res) => {
    const clientState = sdk.getClientState();
    const calls = [];

    for (const [callId, data] of activeCalls.entries()) {
        calls.push({
            call_id: callId,
            has_vox_call: !!data.call,
            has_backend_ws: !!data.ws
        });
    }

    res.json({
        status: clientState === VoxImplant.ClientState.LOGGED_IN ? 'ready' : 'not_ready',
        client_state: clientState,
        active_calls: calls
    });
});

// Start server
async function start() {
    try {
        console.log('[Bridge] Starting Voximplant Bridge Server...');

        await initSDK();

        app.listen(PORT, '0.0.0.0', () => {
            console.log(`[Bridge] ✓ Server listening on port ${PORT}`);
            console.log(`[Bridge] ✓ Ready to accept connection requests`);
            console.log(`[Bridge] Waiting for Backend to call POST /connect...`);
        });
    } catch (error) {
        console.error('[Bridge] Startup error:', error);
        process.exit(1);
    }
}

// Handle shutdown
process.on('SIGINT', () => {
    console.log('[Bridge] Shutting down...');

    // Hangup all active calls
    for (const [callId, data] of activeCalls.entries()) {
        if (data.call) {
            data.call.hangup();
        }
        cleanup(callId);
    }

    process.exit(0);
});

start();
