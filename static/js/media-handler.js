/**
 * Copyright 2025 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

export class MediaHandler {
  constructor() {
    this.videoElement = null;
    this.currentStream = null;
    this.isWebcamActive = false;
    this.isScreenActive = false;
    this.frameCapture = null;
    this.frameCallback = null;
    this.usingFrontCamera = true;
    this.previousFrame = null;
  }

  initialize(videoElement) {
    this.videoElement = videoElement;
  }

  async startWebcam(useFrontCamera = true) {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { 
          width: 1280, 
          height: 720,
          facingMode: useFrontCamera ? "user" : "environment"
        } 
      });
      this.handleNewStream(stream);
      this.isWebcamActive = true;
      this.usingFrontCamera = useFrontCamera;
      return true;
    } catch (error) {
      console.error('Error accessing webcam:', error);
      return false;
    }
  }

  async startScreenShare() {
    try {
      const stream = await navigator.mediaDevices.getDisplayMedia({ 
        video: true 
      });
      this.handleNewStream(stream);
      this.isScreenActive = true;
      
      // Handle when user stops sharing via browser controls
      stream.getVideoTracks()[0].addEventListener('ended', () => {
        this.stopAll();
      });
      
      return true;
    } catch (error) {
      console.error('Error sharing screen:', error);
      return false;
    }
  }

  async switchCamera() {
    if (!this.isWebcamActive) return false;
    const newFacingMode = !this.usingFrontCamera;
    await this.stopAll();
    const success = await this.startWebcam(newFacingMode);
    if (success && this.frameCallback) {
      this.startFrameCapture(this.frameCallback);
    }
    return success;
  }

  handleNewStream(stream) {
    if (this.currentStream) {
      this.stopAll();
    }
    this.currentStream = stream;
    if (this.videoElement) {
      this.videoElement.srcObject = stream;
      this.videoElement.classList.remove('hidden');
    }
  }

  stopAll() {
    if (this.currentStream) {
      this.currentStream.getTracks().forEach(track => track.stop());
      this.currentStream = null;
    }
    if (this.videoElement) {
      this.videoElement.srcObject = null;
      this.videoElement.classList.add('hidden');
    }
    this.isWebcamActive = false;
    this.isScreenActive = false;
    this.stopFrameCapture();
  }

  startFrameCapture(onFrame) {
    this.frameCallback = onFrame;

    const captureFrame = () => {
      if (!this.currentStream || !this.videoElement || this.videoElement.videoWidth === 0) return;

      const canvas = document.createElement('canvas');
      const context = canvas.getContext('2d');
      canvas.width = this.videoElement.videoWidth;
      canvas.height = this.videoElement.videoHeight;

      context.drawImage(this.videoElement, 0, 0, canvas.width, canvas.height);

      const currentHash = this.calculatepHash(canvas);

      if (this.previousFrame) {
        const distance = this.hammingDistance(this.previousFrame, currentHash);
        if (distance <= 1) { // Threshold of 1 is a good starting point
          //console.log(`Hamming distance (${distance}) <= 1, not sending frame.`);
          return;
        } else {
          console.log(`Hamming distance (${distance}) > 1, sending frame.`);
        }
      }

      this.previousFrame = currentHash;

      // Convert to JPEG and base64 encode
      const base64Image = canvas.toDataURL('image/jpeg', 0.8).split(',')[1];
      this.frameCallback(base64Image);
    };

    this.frameCapture = setInterval(captureFrame, 1000);
  }

  calculatepHash(sourceCanvas) {
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    canvas.width = 8;
    canvas.height = 8;
    context.drawImage(sourceCanvas, 0, 0, 8, 8);
    const imageData = context.getImageData(0, 0, 8, 8);
    const grayscale = [];
    for (let i = 0; i < imageData.data.length; i += 4) {
      const r = imageData.data[i];
      const g = imageData.data[i + 1];
      const b = imageData.data[i + 2];
      grayscale.push(0.299 * r + 0.587 * g + 0.114 * b);
    }
    const avg = grayscale.reduce((a, b) => a + b) / grayscale.length;
    return grayscale.map(p => p > avg ? '1' : '0').join('');
  }

  hammingDistance(hash1, hash2) {
    let distance = 0;
    for (let i = 0; i < hash1.length; i++) {
      if (hash1[i] !== hash2[i]) {
        distance++;
      }
    }
    return distance;
  }

  stopFrameCapture() {
    if (this.frameCapture) {
      clearInterval(this.frameCapture);
      this.frameCapture = null;
    }
  }
} 