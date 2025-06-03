# Copyright (c) 2025 Oguzhan Cagirir (OguzhanCOG), KCL Electronics Society
#
# Project: KCL FoAI RoboFootball System
# File: dqn_football_fx8_api.py
# Description: Dummy/Placeholder API for the proprietary FootballFX 8 DQN model.
#              This script provides a structural example of how the advanced DQN
#              could be integrated, using the "footballfx8.bin" weights file.
#              The actual model architecture and inference logic are proprietary.
#
# Author: Oguzhan Cagirir (OguzhanCOG)
# Date: May 24, 2025
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the MIT License as published by
# the Open Source Initiative.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# MIT License for more details.
#
# You should have received a copy of the MIT License
# along with this program. If not, see <https://opensource.org/licenses/MIT>.
#
# --- Version: 8.3.6-dummy ---

import os
import numpy as np
import random
import pygame

MODEL_WEIGHTS_FILENAME = "footballfx8.bin"

class FootballFX8_DQN:
    def __init__(self, model_weights_path="."):
        """
        Initialises the dummy FootballFX 8 DQN API.
        
        In a real scenario, this would load the model architecture and weights.
        Here, it just checks for the placeholder weights file.
        """
        
        self.model_weights_file = os.path.join(model_weights_path, MODEL_WEIGHTS_FILENAME)
        self.model_loaded = False
        self.action_space_example = ["move_random", "target_center_pitch", "target_opponent_goal"]
        self.current_dummy_action_idx = 0

        print("--------------------------------------------------------------------")
        print("INFO: Initialising DUMMY API for proprietary FootballFX 8 DQN Model.")
        if os.path.exists(self.model_weights_file):
            print(f"INFO: Placeholder weights file '{MODEL_WEIGHTS_FILENAME}' found at '{self.model_weights_file}'.")
            self.model_loaded = True
            print("INFO: Dummy model 'loaded' (placeholder).")
        else:
            print(f"WARNING: Placeholder weights file '{MODEL_WEIGHTS_FILENAME}' NOT found at '{self.model_weights_file}'.")
            print("WARNING: Dummy DQN will operate in a very basic fallback mode.")
        print("--------------------------------------------------------------------")

    def _preprocess_state(self, game_state, player_context):
        """
        Dummy state preprocessing.
        
        A real implementation would convert the rich game_state object
        (ball, players, pitch info, and camera view via CNN input)
        into a numerical tensor suitable for the DQN. Redacted.
        """
        
        # Example: Extracting some basic info (not actually used by dummy logic below)
        # ball_pos = game_state['ball'].pos_m if game_state.get('ball') else None
        # player_pos = player_context.pos_m
        # teammate_positions = [t.pos_m for t in game_state.get('teammates', [])]
        # opponent_positions = [o.pos_m for o in game_state.get('opponents', [])]
        # print(f"DQN_DUMMY: Preprocessing state for {player_context} (Ball: {ball_pos})") # Can be spammy; careful!
        return np.random.rand(1, 128)

    def get_action(self, game_state, player_context):
        """
        Dummy action selection.
        
        A real implementation would take the preprocessed state,
        pass it through the FootballFX 8 neural network, and output an action
        (e.g., Q-values for discrete actions, or continuous parameters for movement).

        This dummy version returns a predefined steering target for simplicity,
        mimicking how the Behaviour Tree sets player.primary_steering_target_m.
        """
        
        _ = self._preprocess_state(game_state, player_context) # Call preprocess even if not used

        if not self.model_loaded:
            return player_context.pos_m # Stay still

        # Targets are in world-space meters (simulation coordinates; transformed)
        arena_width_m = game_state.get('arena_width_m', 2.4)
        arena_height_m = game_state.get('arena_height_m', 2.0)
        
        opponent_goal_x = 0.0 if player_context.team == 'B' else arena_width_m

        dummy_targets = [
            pygame.math.Vector2(arena_width_m / 2, arena_height_m / 2),
            pygame.math.Vector2(opponent_goal_x, arena_height_m / 2),
            game_state['ball'].pos_m if game_state.get('ball') else pygame.math.Vector2(random.uniform(0, arena_width_m), random.uniform(0, arena_height_m)),
        ]
        
        has_ball_threshold_m_sq = (player_context.radius_m + game_state['ball'].radius_m + 0.05)**2 if game_state.get('ball') else float('inf')
        
        target_to_return = None
        if game_state.get('ball') and player_context.pos_m.distance_squared_to(game_state['ball'].pos_m) < has_ball_threshold_m_sq:
            target_to_return = dummy_targets[1] # Target opponent goal
            # print(f"DQN_DUMMY ({player_context}): Has ball (conceptual), targeting goal.")
        elif game_state.get('ball'):
            target_to_return = dummy_targets[2] # Target ball
            # print(f"DQN_DUMMY ({player_context}): Targeting ball.")
        else:
            target_to_return = dummy_targets[0] # Target center (fallback if no ball)
            # print(f"DQN_DUMMY ({player_context}): No ball, targeting center.")

        # Add a small random offset to encourage more diverse movement
        # target_to_return += pygame.math.Vector2(random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1))

        return target_to_return

# Example Usage (Illustrative - not meant to be run standalone without a game context!!!)
if __name__ == '__main__':
    print("Illustrative: Initialising FootballFX8_DQN dummy API...")
    # In main.py, you'd pass CFG["SIMULATION_ROOT_DIR"] or similar!
    dqn_agent = FootballFX8_DQN(model_weights_path=".") # Adjust path if needed

    if dqn_agent.model_loaded:
        print("Dummy DQN Agent Initialised (symbolically loaded).")
        # To test get_action, you'd need to mock game_state and player_context
        # This is just a conceptual check.
        class MockPlayer:
            def __init__(self, team, pos_m, radius_m): self.team = team; self.pos_m = pos_m; self.radius_m = radius_m
            def __str__(self): return f"MockPlayer_{self.team}"

        class MockBall:
            def __init__(self, pos_m, radius_m): self.pos_m = pos_m; self.radius_m = radius_m
        
        mock_player = MockPlayer('B', pygame.math.Vector2(1.0, 1.0), 0.065)
        mock_ball = MockBall(pygame.math.Vector2(1.2, 1.0), 0.025)

        mock_game_state = {
            'ball': mock_ball,
            'teammates': [],
            'opponents': [],
            'dt': 0.016,
            'is_designated_ball_winner': True,
            'arena_width_m': 2.4,
            'arena_height_m': 2.0
        }
        action_target = dqn_agent.get_action(mock_game_state, mock_player)
        print(f"Dummy action (steering target) for mock state: {action_target}")
    else:
        print("Dummy DQN Agent initialised, but placeholder weights not found.")