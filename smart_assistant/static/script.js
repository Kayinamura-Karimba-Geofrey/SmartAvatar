const micBtn = document.getElementById('mic-btn');
const sendBtn = document.getElementById('send-btn');
const textInput = document.getElementById('text-input');
const statusText = document.getElementById('status');
const userText = document.getElementById('user-text');
const assistantText = document.getElementById('assistant-text');
const avatar = document.getElementById('avatar');

let isRecording = false;
let mediaRecorder = null;
let audioChunks = [];
let currentAudio = null; // Track playing audio so we can stop it

// Get the best supported MIME type for recording
function getSupportedMimeType() {
    const types = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/mp4'];
    for (const type of types) {
        if (MediaRecorder.isTypeSupported(type)) return type;
    }
    return ''; // Let the browser decide
}

async function startRecording() {
    // Stop any playing audio
    if (currentAudio) {
        currentAudio.pause();
        currentAudio = null;
    }

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const mimeType = getSupportedMimeType();
        const options = mimeType ? { mimeType } : {};

        mediaRecorder = new MediaRecorder(stream, options);
        audioChunks = [];

        mediaRecorder.ondataavailable = (event) => {
            if (event.data && event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        mediaRecorder.onstop = async () => {
            // Stop all tracks to release the microphone
            stream.getTracks().forEach(track => track.stop());

            if (audioChunks.length === 0) {
                statusText.innerText = 'No audio captured';
                return;
            }

            const mimeUsed = mediaRecorder.mimeType || 'audio/webm';
            const ext = mimeUsed.includes('ogg') ? '.ogg' : mimeUsed.includes('mp4') ? '.mp4' : '.webm';
            const audioBlob = new Blob(audioChunks, { type: mimeUsed });
            console.log(`Recorded ${audioBlob.size} bytes as ${mimeUsed}`);

            if (audioBlob.size < 1000) {
                statusText.innerText = 'Audio too short, try again';
                return;
            }

            await sendVoiceData(audioBlob, ext);
        };

        mediaRecorder.onerror = (event) => {
            console.error('MediaRecorder error:', event.error);
            statusText.innerText = 'Recording error';
            isRecording = false;
            micBtn.classList.remove('active');
            avatar.classList.remove('listening');
        };

        // Request data every 250ms to ensure we get chunks
        mediaRecorder.start(250);
        isRecording = true;
        micBtn.classList.add('active');
        avatar.classList.add('listening');
        statusText.innerText = 'Listening...';
        console.log('Recording started with mimeType:', mediaRecorder.mimeType);
    } catch (err) {
        console.error('Mic error:', err);
        statusText.innerText = 'Mic Access Denied';
    }
}

function stopRecording() {
    if (mediaRecorder && isRecording && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        isRecording = false;
        micBtn.classList.remove('active');
        avatar.classList.remove('listening');
        statusText.innerText = 'Processing...';
    }
}

async function sendVoiceData(blob, ext = '.webm') {
    const formData = new FormData();
    formData.append('audio_file', blob, `recording${ext}`);

    try {
        statusText.innerText = 'Processing...';
        const response = await fetch('/voice', {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.error || `Server error: ${response.status}`);
        }

        const transcribed = response.headers.get('X-Transcribed-Text');
        const reply = response.headers.get('X-Response-Text');

        if (transcribed) userText.innerText = transcribed;
        if (reply) assistantText.innerText = reply;

        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        playResponseAudio(audioUrl);

    } catch (error) {
        console.error('Voice send error:', error);
        statusText.innerText = 'Error: ' + error.message;
    }
}

function playResponseAudio(url) {
    if (currentAudio) {
        currentAudio.pause();
    }
    currentAudio = new Audio(url);
    statusText.innerText = 'Speaking...';
    currentAudio.play().catch(err => {
        console.error('Audio playback error:', err);
        statusText.innerText = 'Playback error';
    });
    currentAudio.onended = () => {
        statusText.innerText = 'Ready';
        URL.revokeObjectURL(url); // Free memory
        currentAudio = null;
    };
}

// Text input handler
async function processInput(text) {
    try {
        statusText.innerText = 'Processing...';
        const response = await fetch('/text', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text }),
        });
        const data = await response.json();
        const reply = data.response;
        assistantText.innerText = reply;
        speak(reply);
    } catch (error) {
        console.error('Text error:', error);
        statusText.innerText = 'Error occurred';
    }
}

function speak(text) {
    const synth = window.speechSynthesis;
    if (synth.speaking) synth.cancel();
    const utterThis = new SpeechSynthesisUtterance(text);
    utterThis.onend = () => statusText.innerText = 'Ready';
    statusText.innerText = 'Speaking...';
    synth.speak(utterThis);
}

// Event Listeners
micBtn.addEventListener('click', () => {
    if (isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
});

async function handleTextSubmit() {
    const text = textInput.value.trim();
    if (text) {
        textInput.value = '';
        userText.innerText = text;
        await processInput(text);
    }
}

sendBtn.addEventListener('click', handleTextSubmit);
textInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleTextSubmit();
});
