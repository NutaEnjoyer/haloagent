/**
 * Простой скрипт для подключения к звонку Voximplant
 * Запускается Backend'ом когда нужно подключиться к конференции
 */

const VoxImplant = require('voximplant-websdk');

// Параметры из командной строки
const callId = process.argv[2];

if (!callId) {
    console.error('Usage: node connect-simple.js <call_id>');
    process.exit(1);
}

const VOXIMPLANT_USER = 'firstuser@halodemo.ginai-acc.n3.voximplant.com';
const VOXIMPLANT_PASSWORD = '6S[3rz0X';

const sdk = VoxImplant.getInstance();

async function connect() {
    try {
        console.log(`[Bridge] Connecting to Voximplant for call_id: ${callId}`);

        // Инициализация SDK
        await sdk.init({
            micRequired: true,
            videoSupport: false
        });

        // Подключение к Voximplant
        await sdk.connect();
        console.log(`[Bridge] Connected to Voximplant platform`);

        // Логин
        await sdk.login(VOXIMPLANT_USER, VOXIMPLANT_PASSWORD);
        console.log(`[Bridge] Logged in as ${VOXIMPLANT_USER}`);

        // Делаем вызов к "conference room" используя call_id
        const call = sdk.call({
            number: callId,  // call_id как номер конференции
            video: false,
            customData: JSON.stringify({ call_id: callId })
        });

        call.addEventListener(VoxImplant.CallEvents.Connected, () => {
            console.log(`[Bridge] ✓ Connected to conference ${callId}`);
            console.log(`[Bridge] Audio bridge active - streaming to OpenAI...`);
        });

        call.addEventListener(VoxImplant.CallEvents.Disconnected, () => {
            console.log(`[Bridge] Disconnected from conference`);
            process.exit(0);
        });

        call.addEventListener(VoxImplant.CallEvents.Failed, (e) => {
            console.error(`[Bridge] Call failed:`, e);
            process.exit(1);
        });

        // Держим процесс живым
        process.on('SIGINT', () => {
            console.log(`[Bridge] Hanging up...`);
            call.hangup();
        });

    } catch (error) {
        console.error(`[Bridge] Error:`, error);
        process.exit(1);
    }
}

connect();
