const micBtn = document.getElementById('mic-btn');
const sendBtn = document.getElementById('send-btn');
const textInput = document.getElementById('text-input');
const statusText = document.getElementById('status');
const userText = document.getElementById('user-text');
const assistantText = document.getElementById('assistant-text');
const avatar = document.getElementById('avatar');

// Speech Recognition Setup
window.SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const recognition = new SpeechRecognition();
recognition.interimResults = true;
recognition.lang = 'en-US';

// Speech Synthesis Setup
const synth = window.speechSynthesis;

let isListening = false;

recognition.onstart = () => {
    isListening = true;
    micBtn.classList.add('active');
    avatar.classList.add('listening');
    statusText.innerText = 'Listening...';
};

recognition.onend = () => {
    isListening = false;
    micBtn.classList.remove('active');
    avatar.classList.remove('listening');
    statusText.innerText = 'Processing...';
};

recognition.onresult = (event) => {
    const transcript = Array.from(event.results)
        .map(result => result[0])
        .map(result => result.transcript)
        .join('');

    userText.innerText = transcript;

    if (event.results[0].isFinal) {
        processInput(transcript);
    }
};

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
        statusText.innerText = 'Speaking...';
        
        speak(reply);
    } catch (error) {
        console.error('Error:', error);
        statusText.innerText = 'Error occurred';
    }
}

function speak(text) {
    if (synth.speaking) {
        console.error('speechSynthesis.speaking');
        synth.cancel(); // Stop current speech if any
    }
    
    const utterThis = new SpeechSynthesisUtterance(text);
    utterThis.lang = 'en-US';
    
    utterThis.onend = (event) => {
        statusText.innerText = 'Ready';
    };
    
    utterThis.onerror = (event) => {
        console.error('SpeechSynthesisUtterance.onerror');
        statusText.innerText = 'Error in TTS';
    };

    // Improved voice selection
    const voices = synth.getVoices();
    
    // Filter for English voices
    const englishVoices = voices.filter(v => v.lang.startsWith('en'));
    
    // Priority list for "clear" voices
    const priorityKeywords = ['Google US English', 'Microsoft Aria', 'Microsoft Guy', 'Natural', 'Premium'];
    
    let selectedVoice = null;
    
    for (const keyword of priorityKeywords) {
        selectedVoice = englishVoices.find(v => v.name.includes(keyword));
        if (selectedVoice) break;
    }
    
    // Fallback to any English voice, then to the first available voice
    if (!selectedVoice) {
        selectedVoice = englishVoices[0] || voices[0];
    }

    if (selectedVoice) {
        utterThis.voice = selectedVoice;
        console.log('Selected voice:', selectedVoice.name);
    }

    synth.speak(utterThis);
}

// Event Listeners for Text Input

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
    if (e.key === 'Enter') {
        handleTextSubmit();
    }
});

micBtn.addEventListener('click', () => {
    if (isListening) {
        recognition.stop();
    } else {
        recognition.start();
    }
});

// Load voices when they change (Chrome needs this)
if (speechSynthesis.onvoiceschanged !== undefined) {
    speechSynthesis.onvoiceschanged = () => synth.getVoices();
}
