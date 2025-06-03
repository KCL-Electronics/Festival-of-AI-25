<template>
  <div class="min-h-screen bg-gray-100 p-4 md:p-8">
    <div class="max-w-3xl mx-auto">
      <h1 class="text-2xl md:text-3xl font-bold mb-6 text-gray-800">Webcam Viewer</h1>
      
      <!-- Webcam display -->
      <div class="relative bg-black rounded-lg overflow-hidden shadow-lg mb-6">
        <video 
          ref="videoElement" 
          class="w-full h-auto aspect-video object-cover"
          autoplay 
          playsinline
        ></video>
        
        <!-- Loading overlay -->
        <div v-if="isLoading" class="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50">
          <div class="text-white flex flex-col items-center">
            <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-white mb-2"></div>
            <p>Loading camera...</p>
          </div>
        </div>
        
        <!-- Error message -->
        <div v-if="error" class="absolute inset-0 flex items-center justify-center bg-black bg-opacity-70">
          <div class="text-white text-center p-4">
            <div class="text-red-400 mb-2">
              <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mx-auto mb-2">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12.01" y2="16"></line>
              </svg>
            </div>
            <p class="text-lg font-medium">{{ error }}</p>
            <button 
              @click="initializeCamera" 
              class="mt-4 px-4 py-2 bg-white text-black rounded-md hover:bg-gray-200 transition-colors"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
      
      <!-- Camera selection -->
      <div class="mb-6">
        <label for="camera-select" class="block text-sm font-medium text-gray-700 mb-2">
          Select Camera
        </label>
        <div class="flex gap-4">
          <select 
            id="camera-select" 
            v-model="selectedDeviceId"
            @change="switchCamera"
            class="flex-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
            :disabled="isLoading || !cameras.length"
          >
            <option v-if="!cameras.length" value="" disabled>No cameras available</option>
            <option v-for="camera in cameras" :key="camera.deviceId" :value="camera.deviceId">
              {{ camera.label || `Camera ${camera.deviceId.substring(0, 5)}...` }}
            </option>
          </select>
          
          <button 
            @click="refreshCameraList" 
            class="px-4 py-2 bg-emerald-600 text-white rounded-md hover:bg-emerald-700 transition-colors flex items-center gap-2"
            :disabled="isLoading"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/>
            </svg>
            Refresh
          </button>
        </div>
      </div>
      
      <!-- Status and info -->
      <div class="bg-white rounded-lg p-4 shadow-md">
        <h2 class="text-lg font-medium text-gray-800 mb-2">Camera Information</h2>
        <div v-if="currentCamera" class="text-sm text-gray-600">
          <p><span class="font-medium">Active Camera:</span> {{ currentCamera.label || 'Unknown Camera' }}</p>
          <p><span class="font-medium">Available Cameras:</span> {{ cameras.length }}</p>
        </div>
        <div v-else class="text-sm text-gray-600">
          <p>No active camera</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'

// State
const videoElement = ref(null)
const cameras = ref([])
const selectedDeviceId = ref('')
const currentCamera = ref(null)
const isLoading = ref(true)
const error = ref('')
const stream = ref(null)

// Check if browser supports the required APIs
const isBrowserCompatible = () => {
  return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia && navigator.mediaDevices.enumerateDevices)
}

// Get list of available cameras
const getCameras = async () => {
  try {
    // We need to request camera permission first to get labeled devices
    if (!stream.value) {
      const tempStream = await navigator.mediaDevices.getUserMedia({ video: true })
      tempStream.getTracks().forEach(track => track.stop())
    }
    
    const devices = await navigator.mediaDevices.enumerateDevices()
    const videoDevices = devices.filter(device => device.kind === 'videoinput')
    
    cameras.value = videoDevices
    
    if (videoDevices.length === 0) {
      error.value = 'No cameras detected on your device'
    }
    
    return videoDevices
  } catch (err) {
    console.error('Error enumerating devices:', err)
    error.value = 'Failed to detect cameras'
    return []
  }
}

// Start the camera with the selected device
const startCamera = async (deviceId = null) => {
  try {
    isLoading.value = true
    error.value = ''
    
    // Stop any existing stream
    if (stream.value) {
      stream.value.getTracks().forEach(track => track.stop())
    }
    
    // Set constraints based on available deviceId
    const constraints = {
      video: deviceId ? { deviceId: { exact: deviceId } } : true
    }
    
    // Get the stream
    stream.value = await navigator.mediaDevices.getUserMedia(constraints)
    
    // Set the stream to the video element
    if (videoElement.value) {
      videoElement.value.srcObject = stream.value
    }
    
    // Find the current camera info
    const videoTrack = stream.value.getVideoTracks()[0]
    if (videoTrack) {
      currentCamera.value = {
        label: videoTrack.label,
        deviceId: videoTrack.getSettings().deviceId
      }
      
      // Update selected device ID if it's not already set
      if (!selectedDeviceId.value) {
        selectedDeviceId.value = currentCamera.value.deviceId
      }
    }
    
    isLoading.value = false
    return true
  } catch (err) {
    console.error('Error starting camera:', err)
    
    if (err.name === 'NotAllowedError') {
      error.value = 'Camera access denied. Please allow camera access and try again.'
    } else if (err.name === 'NotFoundError') {
      error.value = 'No camera found. Please connect a camera and try again.'
    } else {
      error.value = `Failed to start camera: ${err.message}`
    }
    
    isLoading.value = false
    return false
  }
}

// Initialize the camera system
const initializeCamera = async () => {
  isLoading.value = true
  error.value = ''
  
  if (!isBrowserCompatible()) {
    error.value = 'Your browser does not support camera access'
    isLoading.value = false
    return
  }
  
  try {
    // Get available cameras
    const videoDevices = await getCameras()
    
    if (videoDevices.length > 0) {
      // If we have a previously selected device and it's still available, use it
      const deviceToUse = selectedDeviceId.value && 
        videoDevices.some(device => device.deviceId === selectedDeviceId.value) 
          ? selectedDeviceId.value 
          : videoDevices[0].deviceId
      
      await startCamera(deviceToUse)
    } else {
      isLoading.value = false
    }
  } catch (err) {
    console.error('Error initializing camera:', err)
    error.value = 'Failed to initialize camera'
    isLoading.value = false
  }
}

// Switch to a different camera
const switchCamera = async () => {
  if (selectedDeviceId.value) {
    await startCamera(selectedDeviceId.value)
  }
}

// Refresh the list of available cameras
const refreshCameraList = async () => {
  await initializeCamera()
}

// Lifecycle hooks
onMounted(() => {
  initializeCamera()
})

onBeforeUnmount(() => {
  // Clean up by stopping all tracks
  if (stream.value) {
    stream.value.getTracks().forEach(track => track.stop())
  }
})
</script>