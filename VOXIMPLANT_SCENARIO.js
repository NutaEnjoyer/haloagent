/**
 * AI Voice Assistant using ASR (low-latency fixed version)
 */

require(Modules.ASR);

var callId = "";
var backendUrl = "https://halo-ai.ru/api";
var webhookUrl = backendUrl + "/voximplant/events";
var greetingMessage = "Здравствуйте! Я голосовой ассистент HALO. Чем могу помочь?";
var systemPrompt = "";

var currentCall = null;
var currentASR = null;

var dialogTurnCount = 0;
var MAX_TURNS = 12;
var isProcessing = false;
var isListening = false;
var isSpeaking = false;  // Track if AI is currently speaking (for barge-in)

/* ===================== APP START ===================== */

VoxEngine.addEventListener(AppEvents.Started, function () {
    Logger.write("[ASR] Scenario started");

    // Get custom data from VoxEngine.customData() method
    var customDataRaw = VoxEngine.customData();
    Logger.write("[ASR] VoxEngine.customData(): " + customDataRaw);

    var targetPhone = "+79019433546";  // Default phone for testing

    // Parse custom data from StartScenarios API
    var customData = null;
    if (customDataRaw) {
        try {
            customData = JSON.parse(customDataRaw);
            Logger.write("[ASR] Parsed customData: " + JSON.stringify(customData));
        } catch (err) {
            Logger.write("[ASR] Failed to parse customData: " + err);
        }
    }

    if (customData) {
        callId = customData.call_id || "";
        backendUrl = customData.webhook_url
            ? customData.webhook_url.replace("/voximplant/events", "")
            : backendUrl;
        webhookUrl = backendUrl + "/voximplant/events";

        // Get target phone from demo session
        if (customData.phone) {
            targetPhone = customData.phone;
            Logger.write("[ASR] Using phone from demo: " + targetPhone);
        }

        // Get greeting and prompt from demo session
        if (customData.greeting) {
            greetingMessage = customData.greeting;
            Logger.write("[ASR] Using custom greeting: " + greetingMessage);
        }

        if (customData.prompt) {
            systemPrompt = customData.prompt;
            Logger.write("[ASR] Using custom prompt (length: " + systemPrompt.length + ")");
        }
    }

    if (!callId) {
        callId = "call_" + Date.now() + "_" + Math.random().toString(36).slice(2, 8);
    }

    sendWebhook("ScenarioStarted");

    Logger.write("[ASR] Calling: " + targetPhone);
    currentCall = VoxEngine.callPSTN(targetPhone, "78652594087");

    currentCall.addEventListener(CallEvents.Connected, onCallConnected);
    currentCall.addEventListener(CallEvents.Disconnected, onCallDisconnected);
    currentCall.addEventListener(CallEvents.Failed, onCallFailed);
});

/* ===================== CALL FLOW ===================== */

function onCallConnected() {
    Logger.write("[ASR] Call connected");
    sendWebhook("CallConnected");

    initASR();

    // Get custom greeting and prompt from backend
    Logger.write("[ASR] Fetching custom greeting from backend...");

    var url = backendUrl + "/voximplant/get_greeting?call_id=" + encodeURIComponent(callId);

    Net.httpRequest(url, function (response) {
        if (response.code === 200) {
            try {
                var data = JSON.parse(response.text);

                if (data.greeting) {
                    greetingMessage = data.greeting;
                    Logger.write("[ASR] Using custom greeting: " + greetingMessage);
                }

                if (data.prompt) {
                    systemPrompt = data.prompt;
                    Logger.write("[ASR] Using custom prompt (length: " + systemPrompt.length + ")");
                }
            } catch (e) {
                Logger.write("[ASR] Failed to parse greeting response: " + e);
            }
        } else {
            Logger.write("[ASR] Failed to get greeting, code=" + response.code);
        }

        // Use greeting (custom or default)
        var greeting = greetingMessage;

        // Save greeting to dialog history on backend
        saveAIMessage(greeting);

        // Speak the greeting
        speak(greeting);
    });
}

function onCallDisconnected() {
    Logger.write("[ASR] Call disconnected");

    try {
        if (currentASR) {
            currentCall.stopMediaTo(currentASR);
            currentASR.stop();
        }
    } catch (e) {}

    sendWebhook("CallDisconnected");
    VoxEngine.terminate();
}

function onCallFailed(e) {
    Logger.write("[ASR] Call failed: " + e.code);
    sendWebhook("CallFailed");
    VoxEngine.terminate();
}

/* ===================== ASR ===================== */

function initASR() {
    Logger.write("[ASR] Initializing ASR (once)");

    // Create ASR with settings optimized for barge-in
    currentASR = VoxEngine.createASR({
        lang: ASRLanguage.RUSSIAN_RU,
        profile: ASRProfileList.GOOGLE_ENHANCED_PHONE_CALL,  // Better for phone calls + echo cancellation
        interimResults: false  // Only final results to reduce false triggers
    });

    // Barge-in: detect when user starts speaking
    currentASR.addEventListener(ASREvents.CaptureStarted, function (e) {
        Logger.write("[ASR] Speech capture started, isSpeaking=" + isSpeaking);

        // If AI is currently speaking, interrupt it immediately
        if (isSpeaking) {
            Logger.write("[ASR] BARGE-IN! User interrupted - stopping AI playback");
            currentCall.stopPlayback();
            isSpeaking = false;
            isProcessing = false;  // Allow processing user's response!
        }
    });

    currentASR.addEventListener(ASREvents.Result, function (e) {
        if (isProcessing) return;

        Logger.write("[ASR] Result: " + e.text);
        currentCall.stopMediaTo(currentASR);
        isListening = false;

        if (!e.text || !e.text.trim()) {
            speak("Извините, я вас не расслышал. Повторите, пожалуйста.");
            return;
        }

        onRecognitionResult(e.text);
    });
}

function startListening() {
    if (!currentASR || isProcessing || isListening) return;

    Logger.write("[ASR] Start listening");

    isListening = true;
    currentCall.sendMediaTo(currentASR);
}

/* ===================== DIALOG ===================== */

function onRecognitionResult(userText) {
    isProcessing = true;
    dialogTurnCount++;

    if (dialogTurnCount > MAX_TURNS) {
        speak("Спасибо за обращение! До свидания.", true);
        return;
    }

    processTextWithAI(userText);
}

/* ===================== BACKEND ===================== */

function saveAIMessage(aiText) {
    Logger.write("[Backend] Saving AI message to history: " + aiText);

    var url =
        backendUrl +
        "/voximplant/save_ai_message?call_id=" +
        encodeURIComponent(callId) +
        "&ai_text=" +
        encodeURIComponent(aiText);

    Net.httpRequest(url, function (response) {
        if (response.code !== 200) {
            Logger.write("[Backend] Failed to save AI message: " + response.code);
        }
    });
}

function processTextWithAI(userText) {
    var requestStart = Date.now();
    Logger.write("[LATENCY-VXI] Starting backend request | user_text_length=" + userText.length);

    var url = backendUrl + "/voximplant/process_text";

    // Prepare POST body with all data
    var postData = {
        call_id: callId,
        user_text: userText
    };

    // Add custom prompt if provided
    if (systemPrompt) {
        postData.prompt = systemPrompt;
    }

    // Send POST request with JSON body
    Net.httpRequestAsync(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        postData: JSON.stringify(postData)
    }).then(function (response) {
        var requestDuration = Date.now() - requestStart;

        if (response.code !== 200) {
            Logger.write("[LATENCY-VXI] ❌ Backend request failed after " + requestDuration + "ms | code=" + response.code);
            handleError();
            return;
        }

        try {
            var data = JSON.parse(response.text);
            var totalDuration = Date.now() - requestStart;

            Logger.write(
                "[LATENCY-VXI] ✅ Backend request completed in " + totalDuration + "ms | " +
                "ai_text_length=" + data.ai_text.length
            );

            speak(data.ai_text);
        } catch (e) {
            Logger.write("[LATENCY-VXI] ❌ Failed to parse response after " + requestDuration + "ms | error=" + e);
            handleError();
        }
    }).catch(function (error) {
        var requestDuration = Date.now() - requestStart;
        Logger.write("[LATENCY-VXI] ❌ Backend request error after " + requestDuration + "ms | error=" + error);
        handleError();
    });
}

/* ===================== TTS ===================== */

function speak(text, hangupAfter) {
    Logger.write("[TTS] Say: " + text);

    isSpeaking = true;  // Mark that AI is speaking
    currentCall.say(text, Language.RU_RUSSIAN_FEMALE);

    // Enable barge-in: start listening while AI speaks
    // ASR profile should handle echo cancellation
    startListening();

    currentCall.addEventListener(
        CallEvents.PlaybackFinished,
        function once() {
            currentCall.removeEventListener(
                CallEvents.PlaybackFinished,
                once
            );

            isSpeaking = false;  // AI finished speaking
            isProcessing = false;

            if (hangupAfter) {
                currentCall.hangup();
            } else if (!isListening) {
                // Restart listening if not already listening
                startListening();
            }
        }
    );
}

/* ===================== ERROR ===================== */

function handleError() {
    speak("Извините, произошла ошибка. Пожалуйста, перезвоните позже.", true);
}

/* ===================== WEBHOOK ===================== */

function sendWebhook(event) {
    try {
        Net.httpRequest(
            webhookUrl +
                "?event=" +
                event +
                "&call_id=" +
                callId +
                "&ts=" +
                Date.now()
        );
    } catch (e) {}
}

function LoggerSafe(msg) {
    try {
        Logger.write("[ASR] " + msg);
    } catch (e) {}
}
