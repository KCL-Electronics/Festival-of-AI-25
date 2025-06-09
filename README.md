# KCL-RIE Festival of AI 2025

## Project Overview
The project for 2025 aims to develop an interactive football game. The system features a hybrid control scheme: two human players each control two robots using mobile phones, while an AI opponent controls another two robots. The primary objective is for teams to score goals against each other.

The setup involves a TV screen acting as a heads-up display for the game, mobile phones as wireless controllers (interfacing with a web-based UI), an overhead camera providing a real-time view for the core simulation, and ESP32-based robots receiving commands via a central server.

## System Architecture & Code
This repository contains the codebase for the KCL FoAI RoboFootball System, which is comprised of several key components:

1.  **Backend Server (`/api`):**
    *   A FastAPI server acting as the central communication hub.
    *   Manages WebSocket connections for:
        *   Mobile phone controllers via the `/ui` (connecting to `/ws/mobile`).
        *   A TV/Heads-Up Display (connecting to `/ws/tv/onloading` for status updates).
        *   Physical ESP32 robots (robots connect as clients to `/ws/robotcontrol`).
        *   The Python simulation's command output (simulation's `ws_client.py` connects to `/ws/mobilecontrol` to send joystick/rotation commands, which are then relayed to the appropriate ESP32 robot).
    *   Dependencies are listed in `/api/requirements.txt`.

2.  **Frontend Interface (`/ui`):**
    *   A Nuxt.js (Vue.js framework) application.
    *   Provides the user interface for the mobile phone controllers.
    *   Likely also serves the interface for the TV heads-up display.
    *   Communicates with the Backend Server (`/api`) via WebSockets.
    *   Frontend dependencies and scripts are managed by `package.json` within the `/ui` directory.

3.  **RoboFootball Simulation (`/simulation`):**
    *   A sophisticated Python-based simulation environment that models the game, controls AI robots, and processes real-world camera input for robot and ball tracking. *This is the primary operational base for game logic and AI.* (Details below)

4.  **ESP32 Robot Firmware (`/esp32`):**
    *   Contains the Arduino C++ firmware (`/esp32/AI_FES_MOVEMENT_TEST/AI_FES_MOVEMENT_TEST.ino`) for the physical ESP32-based robots.
    *   This firmware enables robots to:
        *   Connect to a specified WiFi network.
        *   Establish a WebSocket connection with the `/api` server's `/ws/robotcontrol` endpoint.
        *   Receive JSON-formatted joystick (x, y) and rotation commands.
        *   Control three motors for omni-directional movement based on received commands.

5.  **Dockerisation Support (Root Directory):**
    *   Includes `docker-compose.yml` and `Dockerfile.backend`.
    *   These files facilitate the containerised deployment of the FastAPI backend, simplifying setup and ensuring environment consistency for the server component.

6.  **Line Camera Prototype (`/linecam`):**
    *   Contains scripts (`cctv_fest24.py`, `test_cctv.py`) for a prototype "line camera" system.
    *   This was envisioned to provide a dynamic, football-esque side-view camera feed for display on a large projector at the event venue, simulating a live broadcast CCTV feel. This feature was experimental and not fully integrated into the final game flow.

7.  **Utility & Test Scripts (`/scripts`):**
    *   A collection of miscellaneous scripts. As noted in `/scripts/NOTICE.txt`, this includes deprecated pathfinding algorithms (`raj_bfs.py`, `oze_astar.py`) used for testing or from previous project iterations, and `.ino` files for hardware testing during development.

---

## RoboFootball Simulation (`/simulation` directory)

*(This section details the 6 Python scripts: `setup.py`, `hsv_tuner.py`, `main.py`, `xform_sandbox.py`, `ws_client.py`, `KILL.py`, and their workflow.)*

### Key Components & Workflow:

The simulation relies on a set of interconnected Python scripts:

*   **`setup.py`**:
    *   **Purpose:** Essential pre-requisite utility for calibrating the overhead camera and calculating the perspective transformation matrices.
    *   **Output:** Generates `camera_calibration_{W}x{H}.npz` and `perspective_transform_matrices.npz` files, which are crucial for accurate perception.
    *   **Note:** Must be run successfully before `main.py` or `hsv_tuner.py`.

*   **`hsv_tuner.py`**:
    *   **Purpose:** A utility script for interactively tuning HSV (Hue, Saturation, Value) color thresholds.
    *   **Usage:** Helps identify the correct HSV ranges for detecting the yellow ball under specific lighting conditions using the overhead camera. The output values are then manually used in `main.py`.
    *   **Dependency:** Uses the camera calibration file from `setup.py` for image undistortion.

*   **`main.py`**:
    *   **Purpose:** The central script that runs the entire RoboFootball simulation.
    *   **Features:**
        *   Manages game state (scores, ball position, player positions).
        *   Implements game rules and physics interactions.
        *   Drives the AI for two of the robots using a Behaviour Tree architecture.
        *   Processes real-time data from an overhead camera via a dedicated perception thread:
            *   Detects AprilTags on robots to determine their position and orientation.
            *   Detects the ball using HSV color thresholding.
        *   Utilises `xform_sandbox.py` to translate AI decisions into robot-local joystick commands for WebSocket transmission.
        *   Communicates with `ws_client.py` (via `xform_sandbox.py`) to send commands to physical robots by connecting to the `/api` server's `/ws/mobilecontrol` endpoint.
    *   **Dependencies:** Requires `.npz` files generated by `setup.py` and configured HSV values (tuned with `hsv_tuner.py`).

*   **`xform_sandbox.py`**:
    *   **Purpose:** A utility module responsible for transforming world-space AI target positions into robot-local joystick commands.
    *   **Functionality:**
        *   Calculates normalised joystick commands based on robot position, orientation, and AI target.
        *   Manages the WebSocket client interface (using `ws_client.py`) for sending these commands to the `/api` server.
        *   Includes helper functions for calculating robot orientation from AprilTag corners.

*   **`ws_client.py`**:
    *   **Purpose:** An asynchronous WebSocket client module used by the simulation.
    *   **Functionality:** Handles the connection from the simulation to the `/api` server's `/ws/mobilecontrol` endpoint, allowing joystick commands (from AI or debug tools) to be sent. Manages connection state and message queuing.

*   **`KILL.py`**:
    *   **Purpose:** A simple utility script to immediately halt all connected robots.
    *   **Usage:** Sends a (0,0) joystick command to all configured robot IDs by connecting to the `/api` server via the `ws_client.py` module.

### General Workflow:

1.  **Run `setup.py`**: Calibrate your camera and generate transformation matrices.
2.  **Run `hsv_tuner.py`**: Tune HSV values for ball detection and note them down.
3.  **Update `main.py`**: Transfer the tuned HSV values into the configuration constants within `main.py`.
4.  **Setup & Run Backend/Frontend**: Start the `/api` server and `/ui` frontend (see "Running the System" below). This provides the WebSocket hub.
5.  **Setup ESP32 Robots**: Flash and configure the ESP32 robots so they connect to the `/api` server.
6.  **Run `main.py`**: Start the simulation. The simulation will connect to the `/api` server to send commands for AI-controlled or human-debugged robots. Human players control their robots via mobile phones (interfacing with the `/ui` and `/api`).
7.  **Use `KILL.py`** if an emergency stop for all robots is required.

---

## Advanced AI Model: FootballFX 8 (Proprietary DQN)

While the publicly available `/simulation/main.py` utilises a robust Behaviour Tree (BT) architecture for its AI-controlled robots, an advanced proprietary Deep Q-Network (DQN) model, named **FootballFX 8**, was also developed in-house for this project. This model was employed during the actual event and demonstrated highly competitive and nuanced tactical play.

FootballFX 8 represents a significant research effort, integrating several sophisticated neural network components, including Transformers, dense blocks, and Convolutional Neural Networks (CNNs). These elements enable it to process rich game state information (including direct visual input from the simulated overhead camera view & AprilTag data) to learn and execute incredibly complex, and rich football tactics.

### Motivation for Placeholder API

The full architecture, training methodologies, and specific pre-trained weights for the FootballFX 8 model are currently proprietary and withheld from this public repository, pending formal academic or commercial publication. This approach is standard practice to protect novel research contributions and intellectual property.

The Behaviour Tree implemented in `main.py` serves as a capable and open alternative for public use and experimentation, adapted from internal test runs and designed to provide engaging AI opponents.

### Placeholder API: `dqn_football_fx8_api.py`

To facilitate future integration of the FootballFX 8 model (once it becomes publicly available) or to allow users to experiment with their own advanced Reinforcement Learning (RL) agents, a **dummy/placeholder API script** is provided within the `/simulation` directory:

*   **`/simulation/dqn_football_fx8_api.py`**

**Key features of this dummy API:**

*   **Interface Definition:** It defines a `FootballFX8_DQN` class structure with methods (`__init__`, `_preprocess_state`, `get_action`) that the actual model would expose.
*   **Symbolic Weights Loading:** The script references a `footballfx8.bin` file. *The dummy API only checks for the existence of this file to simulate a "model loaded" state; it does not parse or use its contents.*
*   **Dummy Action Logic:** The `get_action()` method in the dummy API does **not** perform any neural network inference. Instead, it returns pre-defined or simplistic dummy steering targets (as `pygame.math.Vector2` world-space coordinates) to illustrate the expected output.
*   **Purpose:** The primary goal of `dqn_football_fx8_api.py` is to showcase the intended integration point within the simulation and the expected data flow if a DQN-based agent were to replace the Behaviour Tree for AI decision-making.

### Conceptual Integration into `/simulation/main.py`

To integrate an RL agent like FootballFX 8 (or a custom agent adhering to the `dqn_football_fx8_api.py` interface) into the existing `/simulation/main.py`, one would conceptually modify the `Player` class as follows:

1.  **Import and Initialise the Agent (in `Player.__init__`):**
    *   Add the import: `from dqn_football_fx8_api import FootballFX8_DQN` (or your custom agent's class).
    *   For AI-driven players (e.g., `if self.is_ai_driven_by_bt:`), instead of or alongside disabling `self._build_behavior_tree()`, initialise the DQN agent instance:
        ```python
        # Assuming dqn_football_fx8_api.py and footballfx8.bin are in the simulation directory
        self.dqn_agent = FootballFX8_DQN(model_weights_path=".")
        # self.is_ai_driven_by_bt = False # If fully replacing BT
        self.is_ai_driven_by_dqn = True # Add a new flag
        ```

2.  **Modify AI Decision Making (in `Player.update_ai`):**
    *   The `game_state_for_bt` dictionary, which compiles comprehensive game state information (ball, teammates, opponents, etc.), would serve as the input to the DQN agent.
    *   Replace or augment the Behaviour Tree's `tick()` call:
        ```python
        if self.is_ai_driven_by_dqn and hasattr(self, 'dqn_agent'):
            # The dqn_agent.get_action method should return a world-space steering target
            steering_target_m = self.dqn_agent.get_action(game_state_for_bt, self)
            self.primary_steering_target_m = steering_target_m
            # Optional: The DQN might also determine the appropriate slowing_radius
            # self.slowing_radius_for_primary = self.dqn_agent.get_slowing_radius(...)
            log_ai(self, "DQN_ACTION", f"DQN target: {steering_target_m}")
        # elif self.is_ai_driven_by_bt and self.behavior_tree:
        #    bt_status = self.behavior_tree.tick(game_state_for_bt)
        #    ... (existing BT logic to set self.primary_steering_target_m)
        ```
    *   The existing steering behaviours (`_arrive`, `_separation`) and force application (`_apply_steering_force`) within `Player.update_ai` would then use this DQN-derived `self.primary_steering_target_m` to calculate and apply acceleration to the AI player.

**Clarification on `footballfx8.bin`:**
The file `footballfx8.bin`, located in the `/simulation` directory, **contains the actual pre-trained weights** for the proprietary FootballFX 8 model. However, the public `dqn_football_fx8_api.py` (the dummy API) only checks for the *existence* of this file to simulate a "model loaded" state; it does **not** parse or utilise the contents of `footballfx8.bin` because the corresponding model architecture is proprietary and not included in this repository. This allows developers to have the weights on hand for when/if the model architecture is released, or for their own research should they develop a compatible architecture to use these weights.

---

## Running the System

The system comprises multiple independently runnable components that work together.

### 1. Server Backend (API) & Frontend (UI)

To run the FastAPI backend and Vue.js frontend in development mode with hot-reloading (recommended for development):
```sh
npm run dev --prefix ui & uvicorn api.main:app --reload
```
*(Ensure you are in the root directory of the project when running this command. This uses the root `package.json` scripts.)*

Alternatively, for containerised deployment of the backend API:
*   Consult `docker-compose.yml` and `Dockerfile.backend`.
*   Typically, you would run: `docker-compose up --build`

### 2. ESP32 Robot Setup

The physical ESP32 robots require their firmware to be flashed and configured:
1.  Navigate to `/esp32/AI_FES_MOVEMENT_TEST/`.
2.  Open `AI_FES_MOVEMENT_TEST.ino` in the Arduino IDE or a compatible environment like PlatformIO.
3.  **Crucially, update the following variables within the `.ino` file:**
    *   `ssid`: Your WiFi network name.
    *   `password`: Your WiFi password.
    *   `websockets_server_host`: The IP address of the machine running the FastAPI (`/api`) server.
4.  Flash the firmware to each ESP32-based robot.
5.  Power on the robots. They will attempt to connect to the specified WiFi and then to the WebSocket server's `/ws/robotcontrol` endpoint.

### 3. RoboFootball Simulation

1.  Navigate to the `/simulation` directory.
2.  Ensure all Python dependencies (e.g., `pygame`, `opencv-python`, `pupil-apriltags`, `numpy`, `websockets`) are installed in your Python environment. You can typically infer these from the import statements or a `requirements.txt` file if one were added to this directory. ;) (We didn't have time)
3.  Follow the "General Workflow" described in the "RoboFootball Simulation" section above. For example, after completing prerequisites and ensuring the API server is running and ESP32s are connected, run the main simulation:
    ```sh
    python main.py
    ```

---

## Development Notes

This project, particularly the complex `/simulation` environment, was developed with the assistance of **NeuralFusion(TM) III**, an advanced AI model.

The capabilities of NeuralFusion(TM) III, especially its extensive context window and sophisticated attention mechanisms, were instrumental in:
*   Facilitating rapid development and iteration of the intricate game logic, temp AI behaviour trees, and perception systems.
*   Ensuring a high degree of code style consistency and structural coherence across the multiple Python scripts.
*   Managing the complexity of inter-module dependencies and maintaining a clear, functional architecture for the simulation.
This significantly helped in avoiding common pitfalls like context loss or "memory" issues often encountered when developing larger, interconnected systems with AI assistance.

---

## Acknowledgements
*   The initial server-side repo structure (FastAPI & Vue.js in `/api` and `/ui`) is based on a design by Diogo Miguel. You can view his blog post [here](https://dimmaski.com/serve-vue-fastapi/) and the source repo [here](https://github.com/dimmaski/fastapi-vue).
