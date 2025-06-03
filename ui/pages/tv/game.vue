<template>
    <div class="w-screen h-screen bg-green-800 font-black text-white overflow-hidden">
        <!-- Fullscreen Confetti Overlay -->
        <div v-if="showConfetti" class="fixed inset-0 pointer-events-none z-50 overflow-hidden">
            <div v-for="i in 100" :key="i" class="confetti-piece" :style="getConfettiStyle(i)"></div>
        </div>

        <div class="flex flex-col w-4/5 h-screen mx-auto bg-green-600">
            <!-- Game Navigation Bar -->
            <div class="flex items-center justify-center w-[95%] mx-auto my-4 px-2 relative">
                <!-- Centered Score -->
                <div
                    class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-center text-2xl md:text-4xl lg:text-5xl font-bold drop-shadow-lg pointer-events-none select-none w-full">
                    {{ human_score }} : {{ rie_score }}
                </div>
                <!-- Timer (right) -->
                <div class="flex items-center ml-auto px-4 py-2 bg-black bg-opacity-20 rounded-2xl transition-colors duration-300 z-10"
                    :class="{ 'bg-red-700 bg-opacity-70 animate-pulse': timeRemaining <= 10 }">
                    <div class="timer-img w-6 h-6 mr-2"></div>
                    <div class="text-base md:text-xl lg:text-2xl">{{ formatTime(timeRemaining) }}</div>
                </div>
            </div>

            <!-- Game Container -->
            <div class="flex-1 flex w-[95%] mx-auto overflow-hidden">
                <div class="flex-1 flex flex-col gap-4">
                    <!-- Webcam Section -->
                    <div class="relative aspect-video rounded-lg overflow-hidden shadow-lg mb-4">
                        <video ref="videoElement" class="w-full h-full object-cover bg-black" autoplay
                            playsinline></video>

                        <!-- Countdown Overlay -->
                        <div v-if="showCountdown"
                            class="absolute inset-0 flex flex-col items-center justify-center z-10"
                            style="background: rgba(0, 0, 0, 0.5);">
                            <div class="text-8xl md:text-9xl text-white animate-zoom drop-shadow-glow">{{ countdownValue
                            }}</div>
                            <div class="text-2xl md:text-3xl text-white mt-4 drop-shadow-glow">
                                {{ countdownValue > 0 ? 'GET READY!' : 'GO!' }}
                            </div>
                        </div>

                        <!-- Goal Text Overlay -->
                        <div v-if="showGoalText" class="absolute inset-0 flex items-center justify-center z-20"
                            style="background: rgba(0, 0, 0, 0.5);">
                            <div
                                class="goal-text text-8xl md:text-9xl font-extrabold text-white drop-shadow-glow animate-bounce-scale">
                                GOAL!
                            </div>
                        </div>

                        <!-- Loading overlay -->
                        <div v-if="isLoading" class="absolute inset-0 flex items-center justify-center z-10"
                            style="background: rgba(0, 0, 0, 0.5);">
                            <div class="text-center text-white p-4">
                                <div class="spinner"></div>
                                <p>Loading camera...</p>
                            </div>
                        </div>

                        <!-- Error message -->
                        <div v-if="error"
                            class="absolute inset-0 flex items-center justify-center bg-black bg-opacity-70 z-10">
                            <div class="text-center text-white p-4">
                                <div class="text-red-400 mb-2">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24"
                                        fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                                        stroke-linejoin="round" class="mx-auto mb-2">
                                        <circle cx="12" cy="12" r="10"></circle>
                                        <line x1="12" y1="8" x2="12" y2="12"></line>
                                        <line x1="12" y1="16" x2="12.01" y2="16"></line>
                                    </svg>
                                </div>
                                <p class="text-lg font-medium mb-4">{{ error }}</p>
                                <button @click="initializeCamera"
                                    class="px-4 py-2 bg-white text-black rounded hover:bg-gray-200 transition-colors">
                                    Try Again
                                </button>
                            </div>
                        </div>
                    </div>

                    <!-- Controls -->
                    <div class="flex flex-col gap-4">
                        <!-- Game Controls -->
                        <div class="flex gap-2 justify-center">
                            <button @click="isGameRunning ? resetGame() : startGame()"
                                class="px-4 py-3 bg-blue-500 text-white rounded font-bold cursor-pointer transition-colors min-w-20 max-w-30 hover:bg-blue-600 disabled:opacity-60 disabled:cursor-not-allowed"
                                :disabled="isLoading">
                                {{ isGameRunning ? 'Reset' : 'Start' }}
                            </button>
                            <button @click="pauseResumeGame"
                                class="px-4 py-3 bg-orange-500 text-white rounded font-bold cursor-pointer transition-colors min-w-20 max-w-30 hover:bg-orange-600 disabled:opacity-60 disabled:cursor-not-allowed"
                                :disabled="!isGameRunning">
                                {{ isPaused ? 'Resume' : 'Pause' }}
                            </button>
                            <button @click="swapCamera"
                                class="px-4 py-3 bg-purple-600 text-white rounded font-bold cursor-pointer transition-colors min-w-20 max-w-30 hover:bg-purple-700 disabled:opacity-60 disabled:cursor-not-allowed"
                                :disabled="isLoading || cameras.length <= 1">
                                Swap View
                            </button>
                        </div>

                        <!-- Goal Controls -->
                        <div class="flex gap-2 justify-center">
                            <button @click="addGoal('human')"
                                class="px-4 py-3 bg-blue-500 text-white rounded font-bold cursor-pointer transition-colors min-w-25 max-w-35 hover:bg-blue-600 disabled:opacity-60 disabled:cursor-not-allowed"
                                :disabled="!isGameRunning || isPaused">
                                +1 Human
                            </button>
                            <button @click="addGoal('rie')"
                                class="px-4 py-3 bg-red-600 text-white rounded font-bold cursor-pointer transition-colors min-w-25 max-w-35 hover:bg-red-700 disabled:opacity-60 disabled:cursor-not-allowed"
                                :disabled="!isGameRunning || isPaused">
                                +1 AI
                            </button>
                        </div>
                    </div>


                </div>
            </div>

        </div>



        <!-- Quit Confirmation Modal -->
        <div v-if="showQuitConfirm" class="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50">
            <div class="bg-white text-gray-800 rounded-lg p-6 w-[90%] max-w-md text-center">
                <h2 class="text-xl font-bold mb-4">Quit Game?</h2>
                <p class="mb-6">Are you sure you want to quit the current game?</p>
                <div class="flex justify-center gap-4">
                    <button @click="quitGame"
                        class="px-6 py-2 bg-red-500 text-white rounded hover:bg-red-600 transition-colors">
                        Yes, Quit
                    </button>
                    <button @click="showQuitConfirm = false"
                        class="px-6 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 transition-colors">
                        Cancel
                    </button>
                </div>
            </div>
        </div>


    </div>

    <audio ref="bgAudio" :src="audioSrc" autoplay loop hidden></audio>
    <audio ref="scoreSound" :src="scoreSoundSrc" preload="auto" hidden></audio>

</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'

// Path to your MP3 file — adjust as needed
const audioSrc = new URL('@/assets/crowd-sound.mp3', import.meta.url).href

const bgAudio = ref(null)


const scoreSoundSrc = new URL('@/assets/goal.mp3', import.meta.url).href
const scoreSound = ref(null)

onMounted(() => {
    const tryPlay = () => {
        bgAudio.value.play().catch(() => {
            console.warn('Autoplay blocked – waiting for user interaction')

            const resumeOnInteraction = () => {
                bgAudio.value.play()
                window.removeEventListener('click', resumeOnInteraction)
            }

            window.addEventListener('click', resumeOnInteraction)
        })
    }

    tryPlay()
})


// Game state
const human_score = ref(0)
const rie_score = ref(0)

// Timer state
const gameTime = ref(60) // 60 seconds game time
const timeRemaining = ref(gameTime.value)
const isGameRunning = ref(false)
const isPaused = ref(false)
const timerInterval = ref(null)

// Countdown state
const showCountdown = ref(false)
const countdownValue = ref(3)
const countdownInterval = ref(null)

// Goal celebration state
const showConfetti = ref(false)
const showGoalText = ref(false)
const confettiTimeout = ref(null)
const goalTextTimeout = ref(null)

// Camera state
const videoElement = ref(null)
const cameras = ref([])
const selectedDeviceId = ref('')
const currentCamera = ref(null)
const isLoading = ref(true)
const error = ref('')
const stream = ref(null)

// Modal state
const showQuitConfirm = ref(false)

// Format time as MM:SS
const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

// Generate random confetti styles
const getConfettiStyle = (index) => {
    const colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#ffeaa7', '#dda0dd', '#98d8c8', '#f7dc6f', '#ff9ff3', '#feca57', '#ff6b6b', '#48dbfb', '#1dd1a1', '#00d2d3', '#54a0ff', '#5f27cd']
    const randomColor = colors[index % colors.length]
    const randomLeft = Math.random() * 100
    const randomSize = 5 + Math.random() * 10
    const randomDelay = Math.random() * 2
    const randomDuration = 2 + Math.random() * 1

    return {
        backgroundColor: randomColor,
        left: randomLeft + '%',
        width: randomSize + 'px',
        height: randomSize + 'px',
        animationDelay: randomDelay + 's',
        animationDuration: randomDuration + 's'
    }
}

// Add goal for a team
const addGoal = (team) => {

    // Replay from the start if already playing
    scoreSound.value.currentTime = 0
    scoreSound.value.play()

    if (!isGameRunning.value || isPaused.value) return

    if (team === 'human') {
        human_score.value++
    } else if (team === 'rie') {
        rie_score.value++
    }

    // Show goal celebration effects
    showGoalCelebration()
}

// Show goal celebration effects
const showGoalCelebration = () => {
    // Clear any existing timeouts
    if (confettiTimeout.value) clearTimeout(confettiTimeout.value)
    if (goalTextTimeout.value) clearTimeout(goalTextTimeout.value)

    // Show confetti and goal text
    showConfetti.value = true
    showGoalText.value = true

    // Hide confetti after 2 seconds
    confettiTimeout.value = setTimeout(() => {
        showConfetti.value = false
    }, 5000)

    // Hide goal text after 2 seconds
    goalTextTimeout.value = setTimeout(() => {
        showGoalText.value = false
    }, 5000)
}

// Start the game countdown and timer
const startGame = () => {


    if (isGameRunning.value) return

    // Reset game state
    timeRemaining.value = gameTime.value
    isPaused.value = false

    // Start countdown
    showCountdown.value = true
    countdownValue.value = 3

    countdownInterval.value = setInterval(() => {
        countdownValue.value--

        if (countdownValue.value < 0) {

            // Replay from the start if already playing
            scoreSound.value.currentTime = 0
            scoreSound.value.play()

            clearInterval(countdownInterval.value)
            showCountdown.value = false

            // Start the actual game
            isGameRunning.value = true
            startTimer()
        }
    }, 1000)
}

// Start the game timer
const startTimer = () => {
    if (timerInterval.value) clearInterval(timerInterval.value)

    timerInterval.value = setInterval(() => {
        if (timeRemaining.value > 0) {
            timeRemaining.value--
        } else {
            endGame()
        }
    }, 1000)
}

// Pause or resume the game
const pauseResumeGame = () => {
    if (!isGameRunning.value) return

    isPaused.value = !isPaused.value

    if (isPaused.value) {
        clearInterval(timerInterval.value)
    } else {
        startTimer()
    }
}

// End the game
const endGame = () => {
    isGameRunning.value = false
    clearInterval(timerInterval.value)

    // Determine winner and update scores if needed
    // This is where you would add game-end logic

    // Show game over message or transition to results screen
    alert(`Game Over! Final Score: ${human_score.value} - ${rie_score.value}`)
}

// Reset the game
const resetGame = () => {
    // Clean up current game state
    if (timerInterval.value) clearInterval(timerInterval.value)
    if (countdownInterval.value) clearInterval(countdownInterval.value)
    if (confettiTimeout.value) clearTimeout(confettiTimeout.value)
    if (goalTextTimeout.value) clearTimeout(goalTextTimeout.value)

    // Reset all game state
    isGameRunning.value = false
    isPaused.value = false
    showCountdown.value = false
    showConfetti.value = false
    showGoalText.value = false
    timeRemaining.value = gameTime.value

    // Reset scores to 0
    human_score.value = 0
    rie_score.value = 0
}

// Show quit confirmation
const confirmQuit = () => {
    showQuitConfirm.value = true

    // Pause the game while confirmation is shown
    if (isGameRunning.value && !isPaused.value) {
        pauseResumeGame()
    }
}

// Quit the game
const quitGame = () => {
    // Clean up game state
    if (isGameRunning.value) {
        clearInterval(timerInterval.value)
        isGameRunning.value = false
    }

    showQuitConfirm.value = false

    // Here you would typically navigate away or reset the game
    // For now, we'll just reset the timer
    timeRemaining.value = gameTime.value
}

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

// Swap to the next available camera
const swapCamera = async () => {
    if (cameras.value.length <= 1) return;

    // Find the index of the current camera
    const currentIndex = cameras.value.findIndex(camera => camera.deviceId === selectedDeviceId.value);

    // Calculate the next camera index (cycle through the available cameras)
    const nextIndex = (currentIndex + 1) % cameras.value.length;

    // Set the new device ID and switch to it
    selectedDeviceId.value = cameras.value[nextIndex].deviceId;
    await startCamera(selectedDeviceId.value);
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
    // Clean up timers
    if (timerInterval.value) clearInterval(timerInterval.value)
    if (countdownInterval.value) clearInterval(countdownInterval.value)
    if (confettiTimeout.value) clearTimeout(confettiTimeout.value)
    if (goalTextTimeout.value) clearTimeout(goalTextTimeout.value)

    // Clean up camera resources
    if (stream.value) {
        stream.value.getTracks().forEach(track => track.stop())
    }
})
</script>

<style scoped>
@font-face {
    font-family: 'BlackOpsOne-Regular';
    src: url(/fonts/BlackOpsOne-Regular.ttf);
}

.font-black {
    font-family: 'BlackOpsOne-Regular';
}

.timer-img {
    background-image: url(/clock.png);
    background-size: contain;
    background-repeat: no-repeat;
}

/* Confetti animation */
.confetti-piece {
    position: absolute;
    top: -10px;
    animation: confetti-fall linear infinite;
    border-radius: 2px;
}

@keyframes confetti-fall {
    0% {
        transform: translateY(-100vh) rotate(0deg);
        opacity: 1;
    }

    100% {
        transform: translateY(100vh) rotate(360deg);
        opacity: 0;
    }
}

/* Goal text animation */
.goal-text {
    animation: goal-pulse 0.5s infinite alternate;
    text-shadow:
        0 0 10px rgba(255, 255, 255, 0.8),
        0 0 20px rgba(255, 255, 255, 0.5),
        0 0 30px rgba(255, 255, 255, 0.3);
}

@keyframes goal-pulse {
    0% {
        transform: scale(1);
        opacity: 0.8;
    }

    100% {
        transform: scale(1.1);
        opacity: 1;
    }
}

/* Drop shadow glow for text */
.drop-shadow-glow {
    text-shadow:
        0 0 10px rgba(255, 255, 255, 0.8),
        0 0 20px rgba(255, 255, 255, 0.5);
}

/* Zoom animation for countdown */
@keyframes zoom {
    0% {
        transform: scale(0.8);
        opacity: 0.5;
    }

    50% {
        transform: scale(1.2);
        opacity: 1;
    }

    100% {
        transform: scale(0.8);
        opacity: 0.5;
    }
}

.animate-zoom {
    animation: zoom 1s infinite;
}

/* Spinner animation */
.spinner {
    width: 3rem;
    height: 3rem;
    border: 3px solid rgba(255, 255, 255, 0.3);
    border-radius: 50%;
    border-top-color: white;
    animation: spin 1s linear infinite;
    margin: 0 auto 1rem;
}

@keyframes spin {
    to {
        transform: rotate(360deg);
    }
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .goal-text {
        font-size: 5rem;
    }
}
</style>
