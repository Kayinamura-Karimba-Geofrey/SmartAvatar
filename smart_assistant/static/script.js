const micBtn = document.getElementById('mic-btn');
const sendBtn = document.getElementById('send-btn');
const textInput = document.getElementById('text-input');
const statusText = document.getElementById('status');
const userText = document.getElementById('user-text');
const assistantText = document.getElementById('assistant-text');
const avatar = document.getElementById('avatar');

let isRecording = false;
let mediaRecorder;
let audioChunks = [];

// Handle Audio Recording
async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            await sendVoiceData(audioBlob);
        };

        mediaRecorder.start();
        isRecording = true;
        micBtn.classList.add('active');
        avatar.classList.add('listening');
        statusText.innerText = 'Listening...';
    } catch (err) {
        console.error('Error accessing microphone:', err);
        statusText.innerText = 'Mic Access Denied';
    }
}

function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
        isRecording = false;
        micBtn.classList.remove('active');
        avatar.classList.remove('listening');
        statusText.innerText = 'Processing...';
    }
}

async function sendVoiceData(blob) {
    const formData = new FormData();
    formData.append('audio_file', blob, 'recording.webm');

    try {
        const response = await fetch('/voice', {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) throw new Error('Server error');

        const transcribed = response.headers.get('X-Transcribed-Text');
        const reply = response.headers.get('X-Response-Text');

        if (transcribed) userText.innerText = transcribed;
        if (reply) assistantText.innerText = reply;

        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        playResponseAudio(audioUrl);

    } catch (error) {
        console.error('Error sending voice:', error);
        statusText.innerText = 'Error occurred';
    }
}

function playResponseAudio(url) {
    const audio = new Audio(url);
    statusText.innerText = 'Speaking...';
    audio.play();
    audio.onended = () => {
        statusText.innerText = 'Ready';
    };
}

// Handle Text Input (Existing modified to use server response)
async function processInput(text) {
    try {
        const response = await fetch('/text', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: text }),
        });

        const data = await response.json();
        const reply = data.response;
        
        assistantText.innerText = reply;
        
        // For text input, we still use synthesized speech but could also fetch audio from server if we had an endpoint
        // For now, let's use the browser TTS for text input to keep it fast, 
        // OR better yet, we could have a text-to-speech endpoint.
        speak(reply); 
    } catch (error) {
        console.error('Error:', error);
        statusText.innerText = 'Error occurred';
    }
}

// Browser TTS Fallback/Utility
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
        statusText.innerText = 'Processing...';
        await processInput(text);
    }
}

sendBtn.addEventListener('click', handleTextSubmit);
textInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleTextSubmit();
});
