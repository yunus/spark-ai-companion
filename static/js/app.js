/**
 * app.js: JS code for the adk-streaming sample app.
 */

// Import the MediaHandler
import { MediaHandler } from "./media-handler.js";

/**
 * WebSocket handling
 */

// Connect the server with a WebSocket connection
const sessionId = Math.random().toString().substring(10);
const ws_url = "ws://" + window.location.host + "/ws/" + sessionId;
let websocket = null;
let is_audio = true;
let is_screen = false;

// Get DOM elements
// const messageForm = document.getElementById("messageForm");
const messageInput = document.getElementById("message");
//const messagesDiv = document.getElementById("messages");
const sendButton = document.getElementById("sendButton");
let currentMessageId = null;

// Initialize MediaHandler
const mediaHandler = new MediaHandler();
mediaHandler.initialize(document.getElementById("screenShareVideo"));

const messagesContainer = document.getElementById('messages-container');

// Function to get current time for timestamp
const getTimestamp = () => {
    const now = new Date();
    const hours = now.getHours().toString().padStart(2, '0');
    const minutes = now.getMinutes().toString().padStart(2, '0');
    return `${hours}:${minutes}`;
};

// Function to add a new message to the chat
const addMessage = (text, sender, msgId = null) => {
    let pDiv = null;
    let messageDiv = null;
    let previousText = "";
    let newMsgDiv = true;
    if (msgId !== null) {
        let pDivId = "pDiv" + msgId;
        let msgDivId = "msgDiv" + msgId;
        pDiv = document.getElementById(pDivId);
        if (pDiv === null) {
            messageDiv = document.createElement('div');
            messageDiv.id = msgDivId;
            messageDiv.classList.add('message');
            messageDiv.classList.add(sender === 'user' ? 'user-message' : 'bot-message');

            pDiv = document.createElement('p');
            pDiv.id = pDivId;
            messageDiv.appendChild(pDiv);
        } else {
            newMsgDiv = false;
            previousText = document.getElementById(pDivId).textContent;
            messageDiv = document.getElementById(msgDivId);
        }
    } else {
        messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        messageDiv.classList.add(sender === 'user' ? 'user-message' : 'bot-message');
        pDiv = document.createElement('p');
        messageDiv.appendChild(pDiv);
    }
    pDiv.textContent = previousText + text;

    if (newMsgDiv) {
        const timestampSpan = document.createElement('span');
        timestampSpan.classList.add('message-timestamp');
        timestampSpan.textContent = getTimestamp();
        messageDiv.appendChild(timestampSpan);
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
};

// WebSocket handlers
let isConnectionOpen = false;
function connectWebsocket() {
  // Connect websocket
  websocket = new WebSocket(ws_url + "?is_audio=" + is_audio);

  // Handle connection open
  websocket.onopen = function () {
  // Connection opened messages
    isConnectionOpen = true;
    console.log("WebSocket connection opened.");
    //document.getElementById("messages").textContent = "Connection opened";
    addMessage("[Agent Online]", "bot");
    addMessage("How can I help you today?", "bot");

    // Enable the Send button
    document.getElementById("sendButton").disabled = false;
    addSubmitHandler();
  };

  // Handle incoming messages
  websocket.onmessage = function (event) {
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
        // const message = document.createElement("div");
        // message.id = currentMessageId;
        // // Append the message element to the messagesDiv
        // //messagesDiv.appendChild(message);
        // addMessage("", 'bot')
      }

      // Add message text to the existing message element
      // const message = document.getElementById(currentMessageId);
      // Append new data to our raw text store
      // const rawText = (message.dataset.rawText || "Companion: ") + message_from_server.data;
      console.log("rawText:" + message_from_server.data)
      // message.dataset.rawText = rawText;
      addMessage(message_from_server.data, 'bot', currentMessageId);
      // Render the accumulated markdown text into the message element
      //message.innerHTML = marked.parse(rawText);

      // Scroll down to the bottom of the messagesDiv
      //messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
  };

  // Handle connection close
  websocket.onclose = function () {
    console.log("WebSocket connection closed.");
    document.getElementById("sendButton").disabled = true;
    //document.getElementById("messages").textContent = "Connection closed";
    if (isConnectionOpen) {
      addMessage("Agent connection closed", "bot");
      isConnectionOpen = false;
    }
    setTimeout(function () {
      console.log("Reconnecting...");
      connectWebsocket();
    }, 5000);
  };

  websocket.onerror = function (e) {
    console.log("WebSocket error: ", e);
  };
}
connectWebsocket();

function submitChat() {
  const message = messageInput.value;
    if (message) {
      const p = document.createElement("p");
      p.textContent = "> " + message;
      addMessage(message, 'user')
      messageInput.value = "";
      sendMessage({
        mime_type: "text/plain",
        data: message,
      });
      console.log("[CLIENT TO AGENT] " + message);
    }
}

// Add submit handler to the form
function addSubmitHandler() {
  sendButton.addEventListener('click', (e) => {
    e.preventDefault();
    submitChat();
  });
  messageInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          submitChat();
      }
      // Auto-resize the textarea
      messageInput.style.height = 'auto';
      messageInput.style.height = chatInput.scrollHeight + 'px';
  });
}

// Send a message to the server
function sendMessage(message) {
  if (websocket && websocket.readyState == WebSocket.OPEN) {
    const messageJson = JSON.stringify(message);
    websocket.send(messageJson);
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
const INACTIVITY_TIMEOUT = 300000; // in milliseconds

// Function to reset inactivity timer
function resetInactivityTimer() {
  if (inactivityTimer) {
    clearTimeout(inactivityTimer);
  }
  if (is_audio || is_screen) {
    inactivityTimer = setTimeout(() => {
      console.log("Inactivity timeout!!");
      if (is_audio) {
        stopAudio();
        const buttonText = audioButton.querySelector('span:not(.material-icons)');
        // buttonText.textContent = "Start Audio";
        audioButton.classList.remove('active');
        is_audio = false;
        // websocket.close();
        // connectWebsocket();
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
  if (audioPlayerNode == null) {
    startAudioPlayerWorklet().then(([node, ctx]) => {
      audioPlayerNode = node;
      audioPlayerContext = ctx;
    });
  }
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
  // player should continue to play the audio. Stop audio is recorder only.
  // if (audioPlayerNode) {
  //   audioPlayerNode.port.postMessage({ command: "endOfAudio" });
  //   audioPlayerNode.disconnect();
  //   audioPlayerNode = null;
  // }
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
  // const buttonText = audioButton.querySelector('span:not(.material-icons)');
  //if (buttonText.textContent === "Start Audio") {
  if (!audioButton.classList.contains("active")) {
    startAudio();
    is_audio = true;
    // websocket.close(); // close current connection
    // connectWebsocket(); // reconnect with the audio mode
    //buttonText.textContent = "Stop Audio";
    audioButton.classList.add('active');
    resetInactivityTimer(); // Start inactivity timer
  } else {
    stopAudio();
    is_audio = false;
    // websocket.close(); // close current connection
    // connectWebsocket(); // reconnect without audio mode
    //buttonText.textContent = "Start Audio";
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

let sharingScreen = false;

// Start screen sharing
async function startScreenShare() {
  const success = await mediaHandler.startScreenShare();
  if (success) {
    //const buttonText = screenButton.querySelector('span:not(.material-icons)');
    //buttonText.textContent = "Stop Screen Sharing";
    sharingScreen = true;
    is_screen = true;
    // websocket.close(); // close current connection
    // connectWebsocket(); // reconnect with screen sharing mode

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
  //buttonText.textContent = "Start Screen Sharing";
  screenButton.classList.remove('active');
  is_screen = false;
  sharingScreen = false;
  // websocket.close(); // close current connection
  // connectWebsocket(); // reconnect without screen sharing mode
}

// Screen sharing button handling
const screenButton = document.getElementById("screenButton");
screenButton.addEventListener("click", () => {
  const buttonText = screenButton.querySelector('span:not(.material-icons)');
  //if (buttonText.textContent === "Start Screen Sharing") {
  if (!sharingScreen) {
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
