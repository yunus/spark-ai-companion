/**
 * app.js: JS code for the adk-streaming sample app.
 */

// Import the MediaHandler
import { MediaHandler } from "./media-handler.js";

/**
 * SSE (Server-Sent Events) handling
 */

// Connect the server with SSE
const sessionId = Math.random().toString().substring(10);
const sse_url =
  "http://" + window.location.host + "/events/" + sessionId;
const send_url =
  "http://" + window.location.host + "/send/" + sessionId;
let eventSource = null;
let is_audio = false;
let is_screen = false;

// Get DOM elements
const messageForm = document.getElementById("messageForm");
const messageInput = document.getElementById("message");
const messagesDiv = document.getElementById("messages");
let currentMessageId = null;

// Initialize MediaHandler
const mediaHandler = new MediaHandler();
mediaHandler.initialize(document.getElementById("screenShareVideo"));
// SSE handlers
function connectSSE() {
  // Connect to SSE endpoint
  eventSource = new EventSource(sse_url + "?is_audio=" + is_audio);

  // Handle connection open
  eventSource.onopen = function () {
    // Connection opened messages
    console.log("SSE connection opened.");
    document.getElementById("messages").textContent = "Connection opened";

    // Enable the Send button
    document.getElementById("sendButton").disabled = false;
    addSubmitHandler();
  };

  // Handle incoming messages
  eventSource.onmessage = function (event) {
    // Parse the incoming message
    const message_from_server = JSON.parse(event.data);
    //console.log("[AGENT TO CLIENT] ", message_from_server);

    // Check if the turn is complete
    // if turn complete, add new message
    if (
      message_from_server.turn_complete &&
      message_from_server.turn_complete == true
    ) {
      currentMessageId = null;
      return;
    }

    // Check for interrupt message
    if (message_from_server.interrupted && message_from_server.interrupted === true) {
      console.log("Interrupted.");
      // Stop audio playback if it's playing
      if (audioPlayerNode) {
        audioPlayerNode.port.postMessage({ command: "endOfAudio" });
      }
      return;
    }
    
    // If it's audio, play it
    if (message_from_server.mime_type == "audio/pcm" && audioPlayerNode) {
      audioPlayerNode.port.postMessage(base64ToArray(message_from_server.data));
      resetInactivityTimer(); // Reset timer when receiving audio from server
    }

    // If it's a text, print it
    if (message_from_server.mime_type == "text/plain") {
      // Reset timer when receiving text from server
      resetInactivityTimer();

      // add a new message for a new turn
      if (currentMessageId == null) {
        currentMessageId = Math.random().toString(36).substring(7);
        const message = document.createElement("p");
        message.id = currentMessageId;
        // Append the message element to the messagesDiv
        messagesDiv.appendChild(message);
      }

      // Add message text to the existing message element
      const message = document.getElementById(currentMessageId);
      message.textContent += message_from_server.data;

      // Scroll down to the bottom of the messagesDiv
      messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
  };

  // Handle connection close
  eventSource.onerror = function (event) {
    console.log("SSE connection error or closed.");
    document.getElementById("sendButton").disabled = true;
    document.getElementById("messages").textContent = "Connection closed";
    eventSource.close();
    setTimeout(function () {
      console.log("Reconnecting...");
      connectSSE();
    }, 5000);
  };
}
connectSSE();

// Add submit handler to the form
function addSubmitHandler() {
  messageForm.onsubmit = function (e) {
    e.preventDefault();
    const message = messageInput.value;
    if (message) {
      const p = document.createElement("p");
      p.textContent = "> " + message;
      messagesDiv.appendChild(p);
      messageInput.value = "";
      sendMessage({
        mime_type: "text/plain",
        data: message,
      });
      //console.log("[CLIENT TO AGENT] " + message);
    }
    return false;
  };
}

// Send a message to the server via HTTP POST
async function sendMessage(message) {
  try {
    const response = await fetch(send_url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(message)
    });
    
    if (!response.ok) {
      console.error('Failed to send message:', response.statusText);
    }
  } catch (error) {
    console.error('Error sending message:', error);
  }
}

// Decode Base64 data to Array
function base64ToArray(base64) {
  const binaryString = window.atob(base64);
  const len = binaryString.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes.buffer;
}

/**
 * Audio handling
 */

let audioPlayerNode;
let audioPlayerContext;
let audioRecorderNode;
let audioRecorderContext;
let micStream;

// Add inactivity timer variables
let inactivityTimer = null;
const INACTIVITY_TIMEOUT = 30000; // 30 seconds in milliseconds

// Function to reset inactivity timer
function resetInactivityTimer() {
  if (inactivityTimer) {
    clearTimeout(inactivityTimer);
  }
  if (is_audio || is_screen) {
    inactivityTimer = setTimeout(() => {
      if (is_audio) {
        stopAudio();
        const buttonText = audioButton.querySelector('span:not(.material-icons)');
        buttonText.textContent = "Start Audio";
        audioButton.classList.remove('active');
        is_audio = false;
        eventSource.close();
        connectSSE();
      }
      if (is_screen) {
        stopScreenShare();
      }
    }, INACTIVITY_TIMEOUT);
  }
}

// Import the audio worklets
import { startAudioPlayerWorklet } from "./audio-player.js";
import { startAudioRecorderWorklet } from "./audio-recorder.js";

// Start audio
function startAudio() {
  // Start audio output
  startAudioPlayerWorklet().then(([node, ctx]) => {
    audioPlayerNode = node;
    audioPlayerContext = ctx;
  });
  // Start audio input
  startAudioRecorderWorklet(audioRecorderHandler).then(
    ([node, ctx, stream]) => {
      audioRecorderNode = node;
      audioRecorderContext = ctx;
      micStream = stream;
    }
  );
}

// Stop audio
function stopAudio() {
  if (audioPlayerNode) {
    audioPlayerNode.port.postMessage({ command: "endOfAudio" });
    audioPlayerNode.disconnect();
    audioPlayerNode = null;
  }
  if (audioRecorderNode) {
    audioRecorderNode.disconnect();
    audioRecorderNode = null;
  }
  if (audioRecorderContext) {
    audioRecorderContext.close();
    audioRecorderContext = null;
  }
  if (micStream) {
    micStream.getTracks().forEach(track => track.stop());
    micStream = null;
  }
}

// Audio button handling
const audioButton = document.getElementById("audioButton");
audioButton.addEventListener("click", () => {
  const buttonText = audioButton.querySelector('span:not(.material-icons)');
  if (buttonText.textContent === "Start Audio") {
    startAudio();
    is_audio = true;
    eventSource.close(); // close current connection
    connectSSE(); // reconnect with the audio mode
    buttonText.textContent = "Stop Audio";
    audioButton.classList.add('active');
    resetInactivityTimer(); // Start inactivity timer
  } else {
    stopAudio();
    is_audio = false;
    eventSource.close(); // close current connection
    connectSSE(); // reconnect without audio mode
    buttonText.textContent = "Start Audio";
    audioButton.classList.remove('active');
    if (inactivityTimer) {
      clearTimeout(inactivityTimer);
      inactivityTimer = null;
    }
  }
});

// Audio recorder handler
function audioRecorderHandler(pcmData) {
  // Send the pcm data as base64
  sendMessage({
    mime_type: "audio/pcm",
    data: arrayBufferToBase64(pcmData),
  });
  //console.log("[CLIENT TO AGENT] sent %s bytes", pcmData.byteLength);
}

// Encode an array buffer with Base64
function arrayBufferToBase64(buffer) {
  let binary = "";
  const bytes = new Uint8Array(buffer);
  const len = bytes.byteLength;
  for (let i = 0; i < len; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return window.btoa(binary);
}

/**
 * Screen sharing handling
 */

// Start screen sharing
async function startScreenShare() {
  const success = await mediaHandler.startScreenShare();
  if (success) {
    const buttonText = screenButton.querySelector('span:not(.material-icons)');
    buttonText.textContent = "Stop Screen Sharing";
    is_screen = true;
    eventSource.close(); // close current connection
    connectSSE(); // reconnect with screen sharing mode
    
    // Start capturing frames
    mediaHandler.startFrameCapture((base64Image) => {
      // Screen sharing is not counted as activity
      // resetInactivityTimer();

      sendMessage({
        mime_type: "image/jpeg",
        data: base64Image
      });
    });
  }
}

// Stop screen sharing
function stopScreenShare() {
  mediaHandler.stopAll();
  const buttonText = screenButton.querySelector('span:not(.material-icons)');
  buttonText.textContent = "Start Screen Sharing";
  is_screen = false;
  eventSource.close(); // close current connection
  connectSSE(); // reconnect without screen sharing mode
}

// Screen sharing button handling
const screenButton = document.getElementById("screenButton");
screenButton.addEventListener("click", () => {
  const buttonText = screenButton.querySelector('span:not(.material-icons)');
  if (buttonText.textContent === "Start Screen Sharing") {
    startScreenShare();
    screenButton.classList.add('active');
    resetInactivityTimer(); // Start inactivity timer
  } else {
    stopScreenShare();
    screenButton.classList.remove('active');
    if (inactivityTimer) {
      clearTimeout(inactivityTimer);
      inactivityTimer = null;
    }
  }
});
