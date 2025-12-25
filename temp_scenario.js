let callSession = null;
let customData = null;
let webhookUrl = "";

VoxEngine.addEventListener(AppEvents.Started, function(e) {
    Logger.write("=== Scenario Started ===");

    try {
        customData = VoxEngine.customData();
        if (typeof customData === 'string') {
            customData = JSON.parse(customData);
        }

        const callId = customData.call_id;
        const phone = customData.phone;
        const callerId = customData.caller_id;
        webhookUrl = customData.webhook_url;

        Logger.write("Call params: " + callId + " -> " + phone);

        const callerIdClean = callerId.replace(/^\+/, '');
        callSession = VoxEngine.callPSTN(phone, callerIdClean);

        callSession.addEventListener(CallEvents.Connected, onCallConnected);
        callSession.addEventListener(CallEvents.Disconnected, onCallDisconnected);
        callSession.addEventListener(CallEvents.Failed, onCallFailed);

    } catch (error) {
        Logger.write("ERROR: " + error);
        VoxEngine.terminate();
    }
});

function onCallConnected(e) {
    Logger.write("=== Call Connected ===");
    sendWebhook("Connected", "normal");
    callSession.say("Здравствуйте! Я голосовой ассистент HALO.", Language.RU_RUSSIAN_FEMALE);
    setTimeout(function() {
        if (callSession) callSession.hangup();
    }, 10000);
}

function onCallDisconnected(e) {
    Logger.write("=== Call Disconnected ===");
    sendWebhook("Disconnected", "normal");
    VoxEngine.terminate();
}

function onCallFailed(e) {
    Logger.write("=== Call Failed: " + e.code + " - " + e.reason + " ===");
    let reason = "error";
    if (e.code === 486) reason = "busy";
    else if (e.code === 480 || e.code === 408) reason = "no_answer";
    sendWebhook("Failed", reason);
    setTimeout(function() { VoxEngine.terminate(); }, 1000);
}

function sendWebhook(event, reason) {
    if (!webhookUrl) {
        Logger.write("No webhook URL");
        return;
    }
    try {
        var payload = {event: event, call_id: customData.call_id, reason: reason, timestamp: Date.now()};
        var payloadStr = JSON.stringify(payload);
        Logger.write("=== Webhook: " + event + " ===");
        Logger.write("URL: " + webhookUrl);
        Net.httpRequest(webhookUrl, {method: "POST", headers: {"Content-Type": "application/json"}, postData: payloadStr}, function() {});
        Logger.write("Webhook sent");
    } catch (error) {
        Logger.write("Webhook error: " + error);
    }
}