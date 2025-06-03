import pygame
import math
import random
import ws_client
import traceback # Added for logging errors to the file
import time # For WebSocket send timing and log timestamps
import json # For WebSocket payload (used by ws_client)
import threading # For WebSocket client thread (used by ws_client)

# --- IMPORT WEBSOCKET CLIENT ---
# Make sure ws_client.py is in the same directory or adjust path
from ws_client import WebSocketGameClient, init_global_ws_client, shutdown_global_ws_client, ws_game_client

# --- CONFIGURATION ---
_PLAYER_RADIUS_M_VAL = 0.065 # This will be deleted, so don't use directly in functions later
_BALL_RADIUS_M_VAL = 0.025   # This will be deleted
_ARENA_WIDTH_M_VAL = 2.4     # This will be deleted
_ARENA_HEIGHT_M_VAL = 2.0    # This will be deleted
_GOAL_WIDTH_M_VAL = 0.7      # This will be deleted

CFG = {
    "SCREEN_WIDTH": 1920,
    "SCREEN_HEIGHT": 1080,
    "FPS": 30,
    "MARGIN": 50,

    "ARENA_WIDTH_M": _ARENA_WIDTH_M_VAL,
    "ARENA_HEIGHT_M": _ARENA_HEIGHT_M_VAL,
    "PLAYER_RADIUS_M": _PLAYER_RADIUS_M_VAL,
    "BALL_RADIUS_M": _BALL_RADIUS_M_VAL,
    "GOAL_WIDTH_M": _GOAL_WIDTH_M_VAL,
    "GOAL_DEPTH_M": 0.1,

    "PLAYER_MASS": 10.0, "BALL_MASS": 1.0,

    # === PHASE 1 MODIFICATIONS ===
    "PLAYER_ACCELERATION": 15.0,
    "PLAYER_MAX_SPEED": 1.8,
    "PLAYER_DRAG": 4.0,
    "BALL_DAMPING": 0.9,
    # === END PHASE 1 ===

    "RESTITUTION_PLAYER_BALL": 0.6, "RESTITUTION_PLAYER_PLAYER": 0.4, "RESTITUTION_BALL_WALL": 0.7,

    # === PHASE 1 AI MODIFICATIONS ===
    "AI_MAX_SPEED": 1.7,
    "AI_ACCELERATION": 12.0,
    # === END PHASE 1 AI ===
    "AI_MAX_FORCE": 170.0,
    "AI_Slowing_RADIUS_BALL": 0.45,
    "AI_Slowing_RADIUS_POSITION": 0.3,
    "AI_SEPARATION_DISTANCE": _PLAYER_RADIUS_M_VAL * 7.0, # Ok here, CFG is being defined
    # === PHASE 1 & 3 CFG MODIFICATION ===
    "AI_ARRIVAL_THRESHOLD_FACTOR": 0.25,
    "AI_POSITIONING_TARGET_UPDATE_THRESHOLD_FACTOR": 0.5,

    "AI_AT_BALL_FOR_DECISION_M": _PLAYER_RADIUS_M_VAL + _BALL_RADIUS_M_VAL + 0.025, # Ok here

    # === PHASE 1 CFG MODIFICATION ===
    "AI_HAS_BALL_THRESHOLD_M": _PLAYER_RADIUS_M_VAL + _BALL_RADIUS_M_VAL + 0.05, # Ok here
    # === END PHASE 1 ===
    "AI_CAN_KICK_THRESHOLD_M": _PLAYER_RADIUS_M_VAL + _BALL_RADIUS_M_VAL + 0.065, # Ok here
    "AI_KICK_COOLDOWN_FRAMES": 10,

    # === PHASE 2 CFG ADDITIONS FOR SHOOTING ===
    "AI_SHOOTING_MAX_RANGE_M": _ARENA_WIDTH_M_VAL * 0.50, # Ok here
    "AI_SHOOTING_CLEAR_PATH_WIDTH_M": _PLAYER_RADIUS_M_VAL * 1.8, # Ok here
    "AI_SHOOT_MAX_X_OWN_HALF_B": 0.65,
    "AI_SHOOT_MIN_X_OWN_HALF_A": 0.35,
    "AI_SHOOT_FACING_ANGLE_DEGREES": 60.0,
    # === END PHASE 2 CFG ADDITIONS FOR SHOOTING ===

    # === PHASE 2 CFG ADDITIONS FOR DRIBBLING ===
    "AI_DRIBBLE_DISTANCE_FACTOR": 5.0,
    "AI_DRIBBLE_PERSIST_FRAMES": 8,
    "AI_DRIBBLE_PATH_EXTRA_CLEARANCE_M": 0.03,
    "AI_DRIBBLE_GOAL_DIRECTION_BONUS": 0.3,
    # === END PHASE 2 CFG ADDITIONS FOR DRIBBLING ===

    "AI_PASS_MAX_DIST_M": _ARENA_WIDTH_M_VAL * 0.6, # Ok here
    "AI_PASS_MIN_DIST_M": _PLAYER_RADIUS_M_VAL * 5.0, # Ok here
    "AI_PASS_OPENNESS_CHECK_WIDTH_M": _PLAYER_RADIUS_M_VAL * 2.2, # Ok here
    "AI_PASS_TEAMMATE_FORWARD_ADVANTAGE_M": _PLAYER_RADIUS_M_VAL * 3.0, # Ok here

    # === PHASE 3 CFG ADDITIONS FOR CLEARING ===
    "AI_CLEAR_PASS_TEAMMATE_MARKED_RADIUS_FACTOR": 4.5,
    "AI_CLEAR_PASS_MIN_DIST_M": _PLAYER_RADIUS_M_VAL * 4.0, # Ok here
    "AI_CLEAR_PASS_MAX_DIST_M": _ARENA_WIDTH_M_VAL * 0.35,  # Ok here
    "AI_HOOF_CLEARANCE_WIDTH_M": _PLAYER_RADIUS_M_VAL * 1.5, # Ok here
    # === END PHASE 3 CFG ADDITIONS FOR CLEARING ===

    "AI_DEFENSIVE_THIRD_LINE_X_FACTOR_B": 0.70,
    "AI_DEFENSIVE_THIRD_LINE_X_FACTOR_A": 0.30,
    "AI_THREAT_DISTANCE_TO_GOAL_M": _ARENA_WIDTH_M_VAL * 0.40, # Ok here
    "AI_DEFENDER_INTERCEPT_STANDOFF_M": _ARENA_WIDTH_M_VAL * 0.20, # Ok here
    "AI_DEFENDER_COVER_SPACE_OFFSET_M": _PLAYER_RADIUS_M_VAL * 5.0, # Ok here
    # === PHASE 3 CFG ADDITIONS FOR DEFENDER ===
    "AI_DEFENDER_MIN_X_B_FACTOR": 0.45,
    "AI_DEFENDER_MAX_X_A_FACTOR": 0.55, # Corresponds to (1.0 - 0.45)
    "AI_DEF_COVER_PERSIST_FRAMES": 6,
    "AI_DEF_COVER_THREAT_CONE_DOT": 0.1,
    "AI_MIDFIELD_HOLD_BALL_Y_DEADZONE_M": 0.25,
    # === END PHASE 3 CFG ADDITIONS FOR DEFENDER ===

    "AI_BALL_WINNER_PROXIMITY_ADVANTAGE_M": 0.22,

    "AI_ATTACKER_OFFBALL_X_ZONE_MIN_FACTOR": 0.10,
    "AI_ATTACKER_OFFBALL_X_ZONE_MAX_FACTOR": 0.48,
    "AI_ATTACKER_OFFBALL_Y_SPREAD_FACTOR": 0.45,
    "AI_ATTACKER_SUPPORT_BEHIND_BALL_OFFSET_M": _PLAYER_RADIUS_M_VAL * 3.5, # Ok here

    "AI_DEFENDER_MIDFIELD_HOLD_X_FACTOR_B": 0.60,
    "AI_DEFENDER_MIDFIELD_HOLD_X_FACTOR_A": 0.40,

    "AI_WEIGHT_PRIMARY_OBJECTIVE": 1.0, "AI_WEIGHT_SEPARATION": 1.75,

    "COLOR_BACKGROUND": (30,30,30), "COLOR_PITCH": (0,120,0), "COLOR_LINES": (200,200,200),
    "COLOR_TEAM_A": (220,50,50), "COLOR_TEAM_B": (50,100,220), "COLOR_BALL": (255,200,0),
    "COLOR_GOAL": (230,230,230),

    "MAX_SCORE": 5, "RESET_DELAY_MS": 3000,

    "DEBUG_LOG_AI_GENERAL": True,
    "DEBUG_LOG_AI_BT_TICKS": False,
    "DEBUG_LOG_AI_CONDITIONS": True, # Enable for detailed condition checks initially
    "DEBUG_AI_PLAYER_FOCUS_NUM": 0, # 0 for all, or player_num (e.g., 1 or 2 for Team B AI)
    "DEBUG_AI_VELOCITY_VECTORS": False,

    "DEBUG_LOG_GAME_EVENTS": True,
    "DEBUG_LOG_AI_PATHING": False,
    "DEBUG_LOG_AI_DRIBBLE_CHOICE": True,
    "DEBUG_LOG_AI_CLEAR_STRATEGY": True,
    "DEBUG_LOG_AI_STEERING": False, # Set to True to see B1's steering decisions before WS send
}

# --- NEW GLOBAL VARIABLES FOR LOGGING ---
_AI_LOG_FILE_PATH = "ai_game_log.txt"
_ai_log_file_handle = None

# --- CONSTANTS AND UTILS ---
METERS_TO_PIXELS = 1.0
PITCH_RECT_PX = pygame.Rect(0,0,0,0)
GOAL_LINE_THICKNESS_PX = 6
LINE_THICKNESS_PX = 3

def log_ai(player_obj, message_type, message):
    global _ai_log_file_handle
    if not CFG["DEBUG_LOG_AI_GENERAL"]: return

    player_focus_num = CFG.get("DEBUG_AI_PLAYER_FOCUS_NUM", 0)
    is_ai_player = isinstance(player_obj, Player) and player_obj.is_ai

    if player_obj and player_focus_num != 0:
        if is_ai_player and player_obj.player_num != player_focus_num:
            return
        elif not is_ai_player and message_type != "GAME_LOG":
             pass # Allows non-AI player messages if focus is on, unless it's GAME_LOG

    if message_type == "BT_TICK" and not CFG.get("DEBUG_LOG_AI_BT_TICKS", False): return
    if message_type == "CONDITION" and not CFG.get("DEBUG_LOG_AI_CONDITIONS", False): return
    if message_type == "PATH_FAIL" and not CFG.get("DEBUG_LOG_AI_PATHING", False): return
    if message_type == "DRIBBLE_CHOICE" and not CFG.get("DEBUG_LOG_AI_DRIBBLE_CHOICE", False): return
    if message_type == "CLEAR_STRATEGY" and not CFG.get("DEBUG_LOG_AI_CLEAR_STRATEGY", False): return
    if message_type == "STEERING_FORCES" and not CFG.get("DEBUG_LOG_AI_STEERING", False): return

    log_source = f" ({player_obj})" if player_obj else ""
    if _ai_log_file_handle and not _ai_log_file_handle.closed:
        try:
            log_line = f"AI LOG{log_source}: [{message_type}] {message}\n"
            _ai_log_file_handle.write(log_line)
            _ai_log_file_handle.flush()
        except Exception as e:
            print(f"ERROR WRITING TO LOG FILE: {e}")
            print(f"FALLBACK CONSOLE LOG: AI LOG{log_source}: [{message_type}] {message}")
    else:
        print(f"Log file not open. CONSOLE LOG: AI LOG{log_source}: [{message_type}] {message}")

def safe_normalize(vector):
    if vector.length_squared() < 1e-9: return pygame.math.Vector2(0, 0)
    return vector.normalize()

class BTNode:
    def __init__(self, name="Node", player=None):
        self.name = name
        self.player_context = player
        self._status = "FAILURE"
    def get_status(self): return self._status
    def set_status(self, status): self._status = status
    def reset(self):
        self.set_status("FAILURE")
        if hasattr(self, 'children'):
            for child in self.children: child.reset()
    def tick(self, game_state): raise NotImplementedError
    def __str__(self): return f"{self.__class__.__name__}({self.name}, St: {self._status})"

class CompositeNode(BTNode):
    def __init__(self, name, children=None, player=None):
        super().__init__(name, player)
        self.children = children if children is not None else []
        for child in self.children:
            if child.player_context is None: child.player_context = player
        self.running_child_idx = -1
    def add_child(self, child_node):
        if child_node.player_context is None: child_node.player_context = self.player_context
        self.children.append(child_node)
    def reset(self):
        super().reset()
        self.running_child_idx = -1

class Selector(CompositeNode):
    def tick(self, game_state):
        start_idx = 0
        if self.running_child_idx != -1:
            start_idx = self.running_child_idx
        for i in range(start_idx, len(self.children)):
            child = self.children[i]
            if self.running_child_idx != i:
                child.reset()
            child_status = child.tick(game_state)
            if child_status == "SUCCESS" or child_status == "RUNNING":
                self.set_status(child_status)
                self.running_child_idx = i if child_status == "RUNNING" else -1
                return self.get_status()
        self.set_status("FAILURE")
        self.running_child_idx = -1
        return self.get_status()

class Sequence(CompositeNode):
    def tick(self, game_state):
        start_idx = 0
        if self.running_child_idx != -1:
            start_idx = self.running_child_idx
        for i in range(start_idx, len(self.children)):
            child = self.children[i]
            if self.running_child_idx != i:
                 child.reset()
            child_status = child.tick(game_state)
            if child_status == "FAILURE" or child_status == "RUNNING":
                self.set_status(child_status)
                self.running_child_idx = i if child_status == "RUNNING" else -1
                return self.get_status()
        self.set_status("SUCCESS")
        self.running_child_idx = -1
        return self.get_status()

class ActionNode(BTNode):
    def __init__(self, action_name, player=None):
        super().__init__(f"Act_{action_name}", player)
        self.action_true_name = action_name
    def tick(self, game_state):
        log_ai(self.player_context, "BT_TICK", f"Ticking Action: {self.name} (Current status: {self._status})")
        action_method = getattr(self.player_context, f"action_{self.action_true_name}", None)
        if action_method:
            status = action_method(game_state)
            self.set_status(status)
            log_ai(self.player_context, "BT_TICK", f"Action {self.name} new status: {status}")
        else:
            log_ai(self.player_context, "ERROR", f"Action method 'action_{self.action_true_name}' not found for {self.player_context}!")
            self.set_status("FAILURE")
        return self.get_status()

class ConditionNode(BTNode):
    def __init__(self, condition_name, player=None, negate=False):
        super().__init__(f"Cond_{condition_name}{'_Not' if negate else ''}", player)
        self.condition_true_name = condition_name
        self.negate = negate
    def tick(self, game_state):
        condition_method = getattr(self.player_context, f"condition_{self.condition_true_name}", None)
        if condition_method:
            result = condition_method(game_state)
            actual_result = not result if self.negate else result
            self.set_status("SUCCESS" if actual_result else "FAILURE")
            log_ai(self.player_context, "CONDITION", f"{self.name} eval: {result} (negated: {self.negate}) -> {self.get_status()}")
        else:
            log_ai(self.player_context, "ERROR", f"Condition method 'condition_{self.condition_true_name}' not found for {self.player_context}!")
            self.set_status("FAILURE")
        return self.get_status()

class Entity:
    def __init__(self, pos_m, radius_m, mass, color, max_speed_m_s=0, drag=0):
        self.pos_m = pygame.math.Vector2(pos_m)
        self.vel_m_s = pygame.math.Vector2(0, 0)
        self.acc_m_s2 = pygame.math.Vector2(0, 0)
        self.radius_m = radius_m
        self.mass = mass if mass > 1e-6 else 1e-6
        self.color = color
        self.max_speed_m_s = max_speed_m_s
        self.drag = drag
    def get_screen_pos(self):
        return pygame.math.Vector2(
            PITCH_RECT_PX.x + self.pos_m.x * METERS_TO_PIXELS,
            PITCH_RECT_PX.y + self.pos_m.y * METERS_TO_PIXELS)
    def get_screen_radius(self): return self.radius_m * METERS_TO_PIXELS
    def update(self, dt):
        # Special handling for B1 (AI robot controlled via WebSocket)
        # Its acceleration is set to 0 in Player.update_ai if WS is active
        # So, the first part of this block might not apply to B1's self-propulsion

        if self.acc_m_s2.length_squared() > 0: # Applies if acc_m_s2 is not zeroed (e.g. non-B1 AI or human)
             self.vel_m_s += self.acc_m_s2 * dt
        elif self.drag > 0: # Applies drag if no acceleration (or if acc was zeroed for B1)
             self.vel_m_s *= (1 - self.drag * dt)
             if self.vel_m_s.length_squared() < (0.01 * 0.01):
                 self.vel_m_s.update(0,0)
        
        if self.max_speed_m_s > 0 and self.vel_m_s.length_squared() > self.max_speed_m_s**2:
            self.vel_m_s.scale_to_length(self.max_speed_m_s)
        
        self.pos_m += self.vel_m_s * dt
        self.acc_m_s2.update(0, 0) # Reset acceleration for next frame for all entities

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, self.get_screen_pos(), self.get_screen_radius())
        if CFG["DEBUG_AI_VELOCITY_VECTORS"] and self.vel_m_s.length_squared() > 0.01 and \
           isinstance(self, Player) and self.is_ai:
             start_pos_px = self.get_screen_pos()
             end_pos_px = start_pos_px + self.vel_m_s * METERS_TO_PIXELS * 0.3
             pygame.draw.line(screen, (255,255,255), start_pos_px, end_pos_px, 1)

class Player(Entity):
    def __init__(self, pos_m, team_char, player_num):
        self.team = team_char
        self.player_num = player_num
        self.is_ai = (self.team == 'B') # Player B's are AI

        cfg_prefix = "AI_" if self.is_ai else "PLAYER_"
        max_speed = CFG[f"{cfg_prefix}MAX_SPEED"]
        self.acceleration_magnitude = CFG[f"{cfg_prefix}ACCELERATION"]
        drag = CFG["PLAYER_DRAG"]
        color = CFG["COLOR_TEAM_A"] if self.team == 'A' else CFG["COLOR_TEAM_B"]

        super().__init__(pos_m, CFG["PLAYER_RADIUS_M"], CFG["PLAYER_MASS"], color, max_speed, drag)

        self.primary_steering_target_m = None
        self.slowing_radius_for_primary = CFG["AI_Slowing_RADIUS_BALL"]
        self.current_action_name_for_debug = "Idle_Init"
        self.behavior_tree = None
        self._last_has_ball_status = False
        self._last_designated_winner_status = False
        self.kick_cooldown_timer = 0
        # === PHASE 2 & 3 ATTRIBUTES ===
        self.dribble_target_m = None
        self.dribble_target_persists_frames = 0
        self.last_ball_y_for_midfield_hold = -1.0
        self.defensive_cover_target_m = None
        self.defensive_cover_persists_frames = 0
        # === END PHASE 2 & 3 ATTRIBUTES ===

        # --- WEBSOCKET SPECIFIC FOR PLAYER B1 ---
        self.last_ws_send_time_ns = 0
        # Send commands at ~10 Hz. (1 / 10 seconds) * 1_000_000_000 nanoseconds/second
        self.ws_send_interval_ns = int((1.0 / 10.0) * 1_000_000_000) 

        if self.is_ai:
            self.max_force = CFG["AI_MAX_FORCE"]
            self._build_behavior_tree()
            if self.behavior_tree: self.behavior_tree.reset()

    def __str__(self): return f"Player_{self.team}{self.player_num}"

    def _arrive(self, target_pos_m, slowing_radius):
        desired_offset = target_pos_m - self.pos_m
        distance = desired_offset.length()
        if distance > 0.001:
            ramped_speed = self.max_speed_m_s
            if distance < slowing_radius and slowing_radius > 1e-5:
                ramped_speed = self.max_speed_m_s * (distance / slowing_radius)
            desired_velocity = (desired_offset / distance) * ramped_speed
            return desired_velocity - self.vel_m_s
        return pygame.math.Vector2(0, 0)

    def _separation(self, teammates, separation_distance):
        avg_away_dir = pygame.math.Vector2(0, 0)
        count = 0
        for mate in teammates:
            dist_to_mate = self.pos_m.distance_to(mate.pos_m)
            if 1e-5 < dist_to_mate < separation_distance:
                direction = safe_normalize(self.pos_m - mate.pos_m)
                avg_away_dir += direction / (dist_to_mate + 1e-5)
                count += 1
        if count > 0:
            avg_away_dir /= count
            if avg_away_dir.length_squared() > 0:
                desired_sep_velocity = avg_away_dir.normalize() * self.max_speed_m_s
                return desired_sep_velocity - self.vel_m_s
        return pygame.math.Vector2(0, 0)

    def _apply_steering_force(self, steering_force):
        # This method is now only called by non-B1 AI, or B1 if WS is inactive.
        if steering_force.length_squared() > self.max_force**2:
            steering_force.scale_to_length(self.max_force)
        if steering_force.length_squared() > 0:
            self.acc_m_s2 = safe_normalize(steering_force) * self.acceleration_magnitude
        else:
            self.acc_m_s2.update(0,0)

    def set_movement_input(self, direction_vector): # Human
        if direction_vector.length_squared() > 0:
            self.acc_m_s2 = safe_normalize(direction_vector) * self.acceleration_magnitude
        else:
            self.acc_m_s2.update(0,0)

    def _get_game_context_objects(self, game_state):
        ball = game_state['ball']
        teammates = game_state['teammates']
        opponents = game_state['opponents']
        is_designated_ball_winner = game_state.get('is_designated_ball_winner', False)
        my_goal_center = pygame.math.Vector2(CFG["ARENA_WIDTH_M"], CFG["ARENA_HEIGHT_M"] / 2) if self.team == 'B' else pygame.math.Vector2(0, CFG["ARENA_HEIGHT_M"] / 2)
        opponent_goal_center = pygame.math.Vector2(0, CFG["ARENA_HEIGHT_M"] / 2) if self.team == 'B' else pygame.math.Vector2(CFG["ARENA_WIDTH_M"], CFG["ARENA_HEIGHT_M"] / 2)
        return ball, teammates, opponents, my_goal_center, opponent_goal_center, is_designated_ball_winner

    def condition_HasBall(self, game_state):
        ball, _, _, _, _, _ = self._get_game_context_objects(game_state)
        return self.pos_m.distance_squared_to(ball.pos_m) < CFG["AI_HAS_BALL_THRESHOLD_M"]**2

    def condition_CanKickBall(self, game_state):
        if self.kick_cooldown_timer > 0: return False
        ball, _, _, _, _, _ = self._get_game_context_objects(game_state)
        return self.pos_m.distance_squared_to(ball.pos_m) < CFG["AI_CAN_KICK_THRESHOLD_M"]**2

    def condition_TeammateHasBall(self, game_state):
        ball, teammates, _, _, _, _ = self._get_game_context_objects(game_state)
        if teammates:
            return teammates[0].pos_m.distance_squared_to(ball.pos_m) < CFG["AI_HAS_BALL_THRESHOLD_M"]**2
        return False

    def condition_BallInMyDefensiveThird(self, game_state):
        ball, _, _, _, _, _ = self._get_game_context_objects(game_state)
        line_factor = CFG["AI_DEFENSIVE_THIRD_LINE_X_FACTOR_B"] if self.team == 'B' else CFG["AI_DEFENSIVE_THIRD_LINE_X_FACTOR_A"]
        third_line_x = CFG["ARENA_WIDTH_M"] * line_factor
        ball_in_def_third = (ball.pos_m.x > third_line_x if self.team == 'B' else ball.pos_m.x < third_line_x)
        return ball_in_def_third

    def condition_BallInOpponentHalf(self, game_state):
        ball, _, _, _, _, _ = self._get_game_context_objects(game_state)
        return ball.pos_m.x < CFG["ARENA_WIDTH_M"] / 2 if self.team == 'B' else ball.pos_m.x > CFG["ARENA_WIDTH_M"] / 2

    def _is_path_clear(self, start_pos, end_pos, obstacles, clearance_radius):
        path_vec = end_pos - start_pos
        path_len_sq = path_vec.length_squared()
        if path_len_sq < 1e-6: return True
        path_dir = safe_normalize(path_vec)
        path_len = math.sqrt(path_len_sq)
        for obs in obstacles:
            if obs is self: continue
            to_obs_vec = obs.pos_m - start_pos
            proj_scalar = to_obs_vec.dot(path_dir)
            dist_to_line_sq = 0
            if proj_scalar < 0:
                dist_to_line_sq = to_obs_vec.length_squared()
            elif proj_scalar > path_len:
                dist_to_line_sq = (obs.pos_m - end_pos).length_squared()
            else:
                perpendicular_vec = to_obs_vec - (path_dir * proj_scalar)
                dist_to_line_sq = perpendicular_vec.length_squared()
            combined_radius_for_collision = obs.radius_m + clearance_radius
            if dist_to_line_sq < combined_radius_for_collision**2:
                if -obs.radius_m < proj_scalar < path_len + obs.radius_m:
                    if CFG.get("DEBUG_LOG_AI_PATHING", False):
                         log_ai(self, "PATH_FAIL",
                                f"Path [{start_pos.x:.2f},{start_pos.y:.2f}]->[{end_pos.x:.2f},{end_pos.y:.2f}] blocked by {obs} (clr_rad: {clearance_radius:.2f}) for {self.current_action_name_for_debug}")
                    return False
        return True

    def condition_CanShoot(self, game_state):
        ball, _, opponents, my_goal_center, opponent_goal_center, _ = self._get_game_context_objects(game_state)
        if not self.condition_CanKickBall(game_state): return False
        player_focus_check = True
        if self.is_ai :
            player_focus_num = CFG.get("DEBUG_AI_PLAYER_FOCUS_NUM", 0)
            if player_focus_num != 0 and self.player_num != player_focus_num:
                player_focus_check = False
        own_half_shoot_limit_factor_b = CFG.get("AI_SHOOT_MAX_X_OWN_HALF_B", 0.65)
        if self.team == 'B' and self.pos_m.x > CFG["ARENA_WIDTH_M"] * own_half_shoot_limit_factor_b:
            if CFG.get("DEBUG_LOG_AI_CONDITIONS", False) and player_focus_check:
                log_ai(self, "CONDITION", f"CanShoot: False (B player too deep x={self.pos_m.x:.2f} > limit {CFG['ARENA_WIDTH_M'] * own_half_shoot_limit_factor_b:.2f})")
            return False
        dist_to_goal_sq = self.pos_m.distance_squared_to(opponent_goal_center)
        if dist_to_goal_sq > CFG["AI_SHOOTING_MAX_RANGE_M"]**2:
            if CFG.get("DEBUG_LOG_AI_CONDITIONS", False) and player_focus_check:
                log_ai(self, "CONDITION", f"CanShoot: False (out of range {math.sqrt(dist_to_goal_sq):.2f}m > {CFG['AI_SHOOTING_MAX_RANGE_M']:.2f}m)")
            return False
        shoot_facing_angle_rad = math.radians(CFG.get("AI_SHOOT_FACING_ANGLE_DEGREES", 60.0))
        if self.vel_m_s.length_squared() > 0.01:
            dir_to_goal = safe_normalize(opponent_goal_center - self.pos_m)
            if dir_to_goal.length_squared() > 1e-6:
                facing_dir = safe_normalize(self.vel_m_s)
                dot_product = dir_to_goal.dot(facing_dir)
                dot_product = max(-1.0, min(1.0, dot_product))
                if dot_product < math.cos(shoot_facing_angle_rad):
                    if CFG.get("DEBUG_LOG_AI_CONDITIONS", False) and player_focus_check:
                        angle_diff_deg = math.degrees(math.acos(dot_product))
                        log_ai(self, "CONDITION", f"CanShoot: False (not facing goal well enough, angle diff: {angle_diff_deg:.1f} deg > {CFG.get('AI_SHOOT_FACING_ANGLE_DEGREES', 60.0):.1f} deg)")
                    return False
        all_other_players = [p for p in opponents + game_state.get('teammates', []) if p is not self]
        path_is_clear = self._is_path_clear(self.pos_m, opponent_goal_center, all_other_players,
                                   CFG["BALL_RADIUS_M"] + CFG["AI_SHOOTING_CLEAR_PATH_WIDTH_M"]/2)
        if not path_is_clear and CFG.get("DEBUG_LOG_AI_CONDITIONS", False) and player_focus_check:
            log_ai(self, "CONDITION", "CanShoot: False (path not clear)")
        return path_is_clear

    def condition_CanPassToTeammate(self, game_state):
        ball, teammates, opponents, _, _, _ = self._get_game_context_objects(game_state)
        if not teammates or not self.condition_CanKickBall(game_state): return False
        teammate = teammates[0]
        dist_to_teammate = self.pos_m.distance_to(teammate.pos_m)
        if not (CFG["AI_PASS_MIN_DIST_M"] < dist_to_teammate < CFG["AI_PASS_MAX_DIST_M"]): return False
        adv_check = CFG["AI_PASS_TEAMMATE_FORWARD_ADVANTAGE_M"]
        is_teammate_forward = (teammate.pos_m.x < self.pos_m.x - adv_check if self.team == 'B' else teammate.pos_m.x > self.pos_m.x + adv_check)
        if not is_teammate_forward: return False
        return self._is_path_clear(self.pos_m, teammate.pos_m, opponents, ball.radius_m + CFG["AI_PASS_OPENNESS_CHECK_WIDTH_M"]/2)

    def condition_IsDesignatedBallWinner(self, game_state):
        _, _, _, _, _, is_designated_ball_winner = self._get_game_context_objects(game_state)
        return is_designated_ball_winner

    def condition_IsMyGoalThreatened(self, game_state):
        ball, _, opponents, my_goal_center, _, _ = self._get_game_context_objects(game_state)
        is_ball_advancing = (ball.vel_m_s.x > 0.35 if self.team == 'B' else ball.vel_m_s.x < -0.35)
        ball_in_def_third = self.condition_BallInMyDefensiveThird(game_state)
        close_to_goal_sq = ball.pos_m.distance_squared_to(my_goal_center) < CFG["AI_THREAT_DISTANCE_TO_GOAL_M"]**2
        for opp in opponents:
            if opp.pos_m.distance_squared_to(ball.pos_m) < (CFG["AI_HAS_BALL_THRESHOLD_M"] * 1.3)**2:
                if opp.pos_m.distance_squared_to(my_goal_center) < (CFG["AI_THREAT_DISTANCE_TO_GOAL_M"] * 1.2)**2:
                    return True
        return (close_to_goal_sq and (ball_in_def_third or is_ball_advancing))

    def _set_steering_target_for_action(self, target_pos, slowing_radius_key, action_name):
        new_target = pygame.math.Vector2(target_pos)
        log_detail = False
        if self.current_action_name_for_debug != action_name:
            log_detail = True
        elif self.primary_steering_target_m and self.primary_steering_target_m.distance_squared_to(new_target) > (self.radius_m * 0.75)**2:
            log_detail = True
        self.primary_steering_target_m = new_target
        self.slowing_radius_for_primary = CFG[slowing_radius_key]
        if log_detail:
            log_ai(self, "ACTION_INIT", f"Starting/Updating: {action_name}, Target: ({target_pos.x:.2f},{target_pos.y:.2f})")
        self.current_action_name_for_debug = action_name

    def _is_at_target(self, target_threshold_factor=None):
        if target_threshold_factor is None:
            target_threshold_factor = CFG["AI_ARRIVAL_THRESHOLD_FACTOR"]
        if not self.primary_steering_target_m:
            return False
        arrival_threshold_sq = (self.radius_m * target_threshold_factor)**2
        is_arrived = self.pos_m.distance_squared_to(self.primary_steering_target_m) < arrival_threshold_sq
        return is_arrived

    def action_GoToBall(self, game_state):
        ball, _, _, _, _, _ = self._get_game_context_objects(game_state)
        self._set_steering_target_for_action(ball.pos_m, "AI_Slowing_RADIUS_BALL", "GoToBall")
        if self.pos_m.distance_squared_to(ball.pos_m) < CFG["AI_AT_BALL_FOR_DECISION_M"]**2:
            return "SUCCESS"
        return "RUNNING"

    def _execute_kick_action(self, target_pos, action_name, game_state):
        if not self.condition_CanKickBall(game_state): return "FAILURE"
        self.kick_cooldown_timer = CFG["AI_KICK_COOLDOWN_FRAMES"]
        log_ai(self, "ACTION_EVENT", f"{action_name}: KICKED. Cooldown set.")
        if self.behavior_tree: self.behavior_tree.reset()
        return "SUCCESS"

    def action_ShootAtGoal(self, game_state):
        _, _, _, _, opponent_goal_center, _ = self._get_game_context_objects(game_state)
        return self._execute_kick_action(opponent_goal_center, "ShootAtGoal", game_state)

    def action_PassToTeammate(self, game_state):
        _, teammates, _, _, _, _ = self._get_game_context_objects(game_state)
        if not teammates: return "FAILURE"
        return self._execute_kick_action(teammates[0].pos_m, "PassToTeammate", game_state)

    def action_ClearBall(self, game_state):
        if not self.condition_CanKickBall(game_state): return "FAILURE"
        ball, teammates, opponents, _, opponent_goal_center, _ = self._get_game_context_objects(game_state)
        best_clear_target = None
        clear_action_name = "ClearBall_DefaultWide"
        if teammates:
            teammate = teammates[0]
            default_forward_advantage = CFG["PLAYER_RADIUS_M"] * 3.0
            adv_check_clear_pass = CFG.get("AI_PASS_TEAMMATE_FORWARD_ADVANTAGE_M", default_forward_advantage) * 0.7
            is_teammate_forward_for_clear = (teammate.pos_m.x < self.pos_m.x - adv_check_clear_pass if self.team == 'B' else \
                                             teammate.pos_m.x > self.pos_m.x + adv_check_clear_pass)
            if is_teammate_forward_for_clear:
                path_to_teammate_clear = self._is_path_clear(self.pos_m, teammate.pos_m, opponents,
                                                             ball.radius_m + CFG["AI_PASS_OPENNESS_CHECK_WIDTH_M"] / 2)
                if path_to_teammate_clear:
                    teammate_is_open = True
                    teammate_marked_dist_sq = (CFG["PLAYER_RADIUS_M"] * CFG.get("AI_CLEAR_PASS_TEAMMATE_MARKED_RADIUS_FACTOR", 4.5))**2
                    for opp in opponents:
                        if opp.pos_m.distance_squared_to(teammate.pos_m) < teammate_marked_dist_sq:
                            teammate_is_open = False
                            if CFG.get("DEBUG_LOG_AI_CLEAR_STRATEGY", False):
                                log_ai(self, "CLEAR_STRATEGY", f"Teammate {teammate} marked by {opp} for clear pass.")
                            break
                    if teammate_is_open:
                        pass_dist_sq = self.pos_m.distance_squared_to(teammate.pos_m)
                        min_clear_pass_dist_default = CFG["PLAYER_RADIUS_M"] * 4.0
                        max_clear_pass_dist_default = CFG["ARENA_WIDTH_M"] * 0.4
                        min_clear_pass_dist_sq = (CFG.get("AI_CLEAR_PASS_MIN_DIST_M", min_clear_pass_dist_default))**2
                        max_clear_pass_dist_sq = (CFG.get("AI_CLEAR_PASS_MAX_DIST_M", max_clear_pass_dist_default))**2
                        if min_clear_pass_dist_sq < pass_dist_sq < max_clear_pass_dist_sq:
                            best_clear_target = teammate.pos_m
                            clear_action_name = "ClearBall_PassToTeammate"
                            if CFG.get("DEBUG_LOG_AI_CLEAR_STRATEGY", False):
                                log_ai(self, "CLEAR_STRATEGY", f"Attempting CLEARANCE PASS to open teammate {teammate} at ({teammate.pos_m.x:.2f},{teammate.pos_m.y:.2f})")
                        elif CFG.get("DEBUG_LOG_AI_CLEAR_STRATEGY", False):
                             log_ai(self, "CLEAR_STRATEGY", f"Clearance pass to {teammate} not ideal dist ({math.sqrt(pass_dist_sq):.2f}m). Min/Max: {math.sqrt(min_clear_pass_dist_sq):.2f}/{math.sqrt(max_clear_pass_dist_sq):.2f}")
                elif CFG.get("DEBUG_LOG_AI_CLEAR_STRATEGY", False):
                    log_ai(self, "CLEAR_STRATEGY", f"Path to teammate {teammate} for clear pass is not clear.")
        if best_clear_target is None:
            target_x = opponent_goal_center.x
            base_y_offset = CFG["GOAL_WIDTH_M"] * 0.8 + CFG["ARENA_HEIGHT_M"] * 0.20
            random_factor = random.uniform(0.9, 1.3)
            final_y_offset = base_y_offset * random_factor
            candidate_y1 = CFG["ARENA_HEIGHT_M"] / 2 + final_y_offset
            candidate_y2 = CFG["ARENA_HEIGHT_M"] / 2 - final_y_offset
            preferred_target_y = candidate_y1 if self.pos_m.y < CFG["ARENA_HEIGHT_M"] / 2 else candidate_y2
            alternate_target_y = candidate_y2 if self.pos_m.y < CFG["ARENA_HEIGHT_M"] / 2 else candidate_y1
            preferred_target = pygame.math.Vector2(target_x, preferred_target_y)
            alternate_target = pygame.math.Vector2(target_x, alternate_target_y)
            preferred_target.y = max(ball.radius_m * 1.5, min(preferred_target.y, CFG["ARENA_HEIGHT_M"] - ball.radius_m * 1.5))
            alternate_target.y = max(ball.radius_m * 1.5, min(alternate_target.y, CFG["ARENA_HEIGHT_M"] - ball.radius_m * 1.5))
            default_hoof_clearance = CFG["PLAYER_RADIUS_M"] * 1.5
            hoof_clearance_width = CFG.get("AI_HOOF_CLEARANCE_WIDTH_M", default_hoof_clearance)
            path_to_preferred_clear = self._is_path_clear(self.pos_m, preferred_target, opponents, ball.radius_m + hoof_clearance_width / 2)
            path_to_alternate_clear = self._is_path_clear(self.pos_m, alternate_target, opponents, ball.radius_m + hoof_clearance_width / 2)
            if path_to_preferred_clear and path_to_alternate_clear:
                best_clear_target = preferred_target if abs(preferred_target.y - self.pos_m.y) > abs(alternate_target.y - self.pos_m.y) else alternate_target
                clear_action_name = "ClearBall_WideChosen"
            elif path_to_preferred_clear:
                best_clear_target = preferred_target
                clear_action_name = "ClearBall_WidePreferred"
            elif path_to_alternate_clear:
                best_clear_target = alternate_target
                clear_action_name = "ClearBall_WideAlternate"
            else:
                best_clear_target = opponent_goal_center
                clear_action_name = "ClearBall_DesperateToGoal"
                if CFG.get("DEBUG_LOG_AI_CLEAR_STRATEGY", False): log_ai(self, "CLEAR_STRATEGY", "No clear wide option, desperate clear towards goal center.")
            if CFG.get("DEBUG_LOG_AI_CLEAR_STRATEGY", False) and "Wide" in clear_action_name:
                 log_ai(self, "CLEAR_STRATEGY", f"Attempting {clear_action_name} towards ({best_clear_target.x:.2f},{best_clear_target.y:.2f})")
        return self._execute_kick_action(best_clear_target, clear_action_name, game_state)

    def action_DribbleStrategically(self, game_state):
        if not self.condition_HasBall(game_state):
            self.dribble_target_m = None
            self.dribble_target_persists_frames = 0
            return "FAILURE"
        ball, _, opponents, _, opponent_goal_center, _ = self._get_game_context_objects(game_state)
        recalculate_target = False
        if self.dribble_target_m is None or self.dribble_target_persists_frames <= 0:
            recalculate_target = True
        elif self.primary_steering_target_m and \
             self.pos_m.distance_squared_to(self.primary_steering_target_m) < (self.radius_m * CFG["AI_ARRIVAL_THRESHOLD_FACTOR"] * 0.7)**2:
            recalculate_target = True
            if CFG.get("DEBUG_LOG_AI_DRIBBLE_CHOICE", False):
                log_ai(self, "DRIBBLE_CHOICE", f"Dribble step to old target ({self.primary_steering_target_m.x:.2f},{self.primary_steering_target_m.y:.2f}) completed. Recalculating.")
        action_debug_name_suffix = self.current_action_name_for_debug
        if recalculate_target:
            best_dribble_target = None
            max_openness = -float('inf')
            dribble_attempt_distance = self.radius_m * CFG.get("AI_DRIBBLE_DISTANCE_FACTOR", 5.0)
            angle_candidates = [0, -25, 25, -50, 50, -75, 75]
            for angle_offset in angle_candidates:
                dir_to_goal_base = safe_normalize(opponent_goal_center - self.pos_m)
                if dir_to_goal_base.length_squared() < 1e-6:
                    dribble_dir = pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize()
                else:
                    dribble_dir = dir_to_goal_base.rotate(angle_offset)
                potential_target = self.pos_m + dribble_dir * dribble_attempt_distance
                potential_target.x = max(self.radius_m * 1.1, min(potential_target.x, CFG["ARENA_WIDTH_M"] - self.radius_m * 1.1))
                potential_target.y = max(self.radius_m * 1.1, min(potential_target.y, CFG["ARENA_HEIGHT_M"] - self.radius_m * 1.1))
                all_other_players = opponents + game_state.get('teammates', [])
                obstacles_for_dribble = [p for p in all_other_players if p is not self]
                dribble_path_clearance = self.radius_m + CFG["BALL_RADIUS_M"] + CFG.get("AI_DRIBBLE_PATH_EXTRA_CLEARANCE_M", 0.03)
                if self._is_path_clear(self.pos_m, potential_target, obstacles_for_dribble, dribble_path_clearance):
                    min_dist_to_any_player_sq = float('inf')
                    for p_other in obstacles_for_dribble:
                        min_dist_to_any_player_sq = min(min_dist_to_any_player_sq, potential_target.distance_squared_to(p_other.pos_m))
                    openness_score = math.sqrt(min_dist_to_any_player_sq)
                    dir_to_potential_target = safe_normalize(potential_target - self.pos_m)
                    if dir_to_goal_base.length_squared() > 0:
                         openness_score += dir_to_potential_target.dot(dir_to_goal_base) * CFG.get("AI_DRIBBLE_GOAL_DIRECTION_BONUS", 0.3)
                    if openness_score > max_openness:
                        max_openness = openness_score
                        best_dribble_target = potential_target
            if best_dribble_target is None:
                if CFG.get("DEBUG_LOG_AI_DRIBBLE_CHOICE", False):
                    log_ai(self, "DRIBBLE_CHOICE", "No clear strategic dribble target, trying short forward nudge.")
                default_dribble_dir = safe_normalize(opponent_goal_center - self.pos_m)
                if default_dribble_dir.length_squared() < 1e-6:
                    default_dribble_dir = pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize()
                self.dribble_target_m = self.pos_m + default_dribble_dir * (self.radius_m * 2.0)
                action_debug_name_suffix = "DribbleStrategically_Default"
            else:
                self.dribble_target_m = best_dribble_target
                if CFG.get("DEBUG_LOG_AI_DRIBBLE_CHOICE", False):
                    log_ai(self, "DRIBBLE_CHOICE", f"New best dribble target: ({self.dribble_target_m.x:.2f},{self.dribble_target_m.y:.2f}) with openness: {max_openness:.2f}")
                action_debug_name_suffix = "DribbleStrategically_NewTgt"
            self.dribble_target_persists_frames = CFG.get("AI_DRIBBLE_PERSIST_FRAMES", 8)
            self._set_steering_target_for_action(self.dribble_target_m, "AI_Slowing_RADIUS_BALL", action_debug_name_suffix)
        else:
            self._set_steering_target_for_action(self.dribble_target_m, "AI_Slowing_RADIUS_BALL", "DribbleStrategically_Persist")
        self.dribble_target_persists_frames -= 1
        if self._is_at_target(target_threshold_factor=CFG["AI_ARRIVAL_THRESHOLD_FACTOR"] * 0.8):
            if CFG.get("DEBUG_LOG_AI_DRIBBLE_CHOICE", False):
                log_ai(self, "DRIBBLE_CHOICE", f"Dribble step to ({self.dribble_target_m.x:.2f},{self.dribble_target_m.y:.2f}) SUCCESS. BT will re-evaluate.")
            self.dribble_target_m = None
            self.dribble_target_persists_frames = 0
            return "SUCCESS"
        return "RUNNING"

    def _move_to_position_action(self, target_pos, action_name, game_state, slowing_radius_key="AI_Slowing_RADIUS_POSITION"):
        target_changed_significantly = True
        if self.primary_steering_target_m and self.current_action_name_for_debug == action_name :
             dist_sq_threshold = (self.radius_m * CFG.get("AI_POSITIONING_TARGET_UPDATE_THRESHOLD_FACTOR", 0.5))**2
             if self.primary_steering_target_m.distance_squared_to(target_pos) <= dist_sq_threshold:
                 target_changed_significantly = False
        if self.current_action_name_for_debug != action_name or target_changed_significantly:
            self._set_steering_target_for_action(target_pos, slowing_radius_key, action_name)
        if self._is_at_target(target_threshold_factor=CFG["AI_ARRIVAL_THRESHOLD_FACTOR"]):
            return "SUCCESS"
        return "RUNNING"

    def action_MoveToAttackingSupport(self, game_state):
        ball, teammates, _, opponent_goal_center, _, _ = self._get_game_context_objects(game_state)
        ref_pos = ball.pos_m
        teammate_with_ball_flag = self.condition_TeammateHasBall(game_state)
        if teammate_with_ball_flag and teammates: ref_pos = teammates[0].pos_m
        target_x_min = CFG["ARENA_WIDTH_M"] * CFG["AI_ATTACKER_OFFBALL_X_ZONE_MIN_FACTOR"]
        target_x_max = CFG["ARENA_WIDTH_M"] * CFG["AI_ATTACKER_OFFBALL_X_ZONE_MAX_FACTOR"]
        x_offset = CFG["PLAYER_RADIUS_M"] * (7 if teammate_with_ball_flag else 4)
        target_x = ref_pos.x - x_offset if self.team == 'B' else ref_pos.x + x_offset
        target_x = max(target_x_min, min(target_x, target_x_max))
        y_spread = CFG["ARENA_HEIGHT_M"] * CFG["AI_ATTACKER_OFFBALL_Y_SPREAD_FACTOR"]
        if ref_pos.y < CFG["ARENA_HEIGHT_M"] / 3:
            target_y = CFG["ARENA_HEIGHT_M"] * 0.66
        elif ref_pos.y > CFG["ARENA_HEIGHT_M"] * (2/3):
            target_y = CFG["ARENA_HEIGHT_M"] * 0.33
        else:
            target_y = self.pos_m.y + (y_spread if self.pos_m.y < CFG["ARENA_HEIGHT_M"] / 2 else -y_spread)
        target_y = max(self.radius_m * 2, min(target_y, CFG["ARENA_HEIGHT_M"] - self.radius_m * 2))
        final_target = pygame.math.Vector2(target_x, target_y)
        return self._move_to_position_action(final_target, "MoveToAttackingSupport", game_state)

    def action_MoveToDefensiveCover(self, game_state):
        ball, _, opponents, my_goal_center, _, _ = self._get_game_context_objects(game_state)
        action_name_base = "MoveToDefensiveCover"
        player_focus_check = (CFG.get("DEBUG_AI_PLAYER_FOCUS_NUM",0) in [0, self.player_num])
        recalculate_target = False
        if self.defensive_cover_target_m is None or self.defensive_cover_persists_frames <= 0:
            recalculate_target = True
        elif self.defensive_cover_target_m and ball.pos_m.distance_squared_to(self.defensive_cover_target_m) > (CFG["ARENA_WIDTH_M"]*0.3)**2 :
            recalculate_target = True
            if CFG.get("DEBUG_LOG_AI_STEERING", False) and player_focus_check:
                log_ai(self, "DEF_COVER", "Ball moved significantly, recalculating cover target.")
        if recalculate_target:
            dir_ball_to_my_goal = safe_normalize(my_goal_center - ball.pos_m)
            if dir_ball_to_my_goal.length_squared() < 1e-6:
                dir_ball_to_my_goal = pygame.math.Vector2(-1 if self.team == 'B' else 1, 0)
            standoff_dist = CFG["AI_DEFENDER_INTERCEPT_STANDOFF_M"]
            target_pos_behind_ball = ball.pos_m + dir_ball_to_my_goal * standoff_dist
            final_target_pos = target_pos_behind_ball
            most_threatening_opp = None
            min_threat_score = float('inf')
            for opp in opponents:
                dist_opp_ball_sq = opp.pos_m.distance_squared_to(ball.pos_m)
                dist_opp_goal_sq = opp.pos_m.distance_squared_to(my_goal_center)
                vec_ball_to_opp_dir = safe_normalize(opp.pos_m - ball.pos_m)
                is_opp_goal_side_of_ball = vec_ball_to_opp_dir.dot(dir_ball_to_my_goal) > CFG.get("AI_DEF_COVER_THREAT_CONE_DOT", 0.1)
                if is_opp_goal_side_of_ball and dist_opp_ball_sq < (CFG["ARENA_WIDTH_M"] * 0.35)**2 :
                    threat_score = dist_opp_goal_sq * 0.7 + dist_opp_ball_sq * 0.3
                    if threat_score < min_threat_score:
                        min_threat_score = threat_score
                        most_threatening_opp = opp
            if most_threatening_opp:
                dir_threat_to_goal = safe_normalize(my_goal_center - most_threatening_opp.pos_m)
                cover_point_threat = most_threatening_opp.pos_m + dir_threat_to_goal * (self.radius_m * 2.0)
                final_target_pos = target_pos_behind_ball * 0.4 + cover_point_threat * 0.6
                if CFG.get("DEBUG_LOG_AI_STEERING", False) and player_focus_check:
                     log_ai(self, "DEF_COVER", f"Covering threat {most_threatening_opp}, blended target to ({final_target_pos.x:.2f}, {final_target_pos.y:.2f}).")
            else:
                final_target_pos = ball.pos_m + dir_ball_to_my_goal * (standoff_dist + CFG["AI_DEFENDER_COVER_SPACE_OFFSET_M"])
                if CFG.get("DEBUG_LOG_AI_STEERING", False) and player_focus_check:
                     log_ai(self, "DEF_COVER", f"No specific threat, general space cover to ({final_target_pos.x:.2f}, {final_target_pos.y:.2f}).")
            min_x_b = CFG["ARENA_WIDTH_M"] * CFG.get("AI_DEFENDER_MIN_X_B_FACTOR", 0.45)
            max_x_a = CFG["ARENA_WIDTH_M"] * (1.0 - CFG.get("AI_DEFENDER_MIN_X_B_FACTOR", 0.45))
            if self.team == 'B':
                final_target_pos.x = max(min_x_b, min(final_target_pos.x, my_goal_center.x - self.radius_m * 1.0))
            else:
                final_target_pos.x = min(max_x_a, max(final_target_pos.x, my_goal_center.x + self.radius_m * 1.0))
            final_target_pos.y = max(self.radius_m * 1.5, min(final_target_pos.y, CFG["ARENA_HEIGHT_M"] - self.radius_m * 1.5))
            self.defensive_cover_target_m = final_target_pos
            self.defensive_cover_persists_frames = CFG.get("AI_DEF_COVER_PERSIST_FRAMES", 6)
            action_name_base = f"{action_name_base}_NewTgt"
        else:
            action_name_base = f"{action_name_base}_Persist"
        self.defensive_cover_persists_frames -= 1
        return self._move_to_position_action(self.defensive_cover_target_m, action_name_base, game_state)

    def action_HoldMidfieldLine(self, game_state):
        ball, _, _, _, _, _ = self._get_game_context_objects(game_state)
        target_x_factor = CFG["AI_DEFENDER_MIDFIELD_HOLD_X_FACTOR_B"] if self.team == 'B' else CFG["AI_DEFENDER_MIDFIELD_HOLD_X_FACTOR_A"]
        target_x = CFG["ARENA_WIDTH_M"] * target_x_factor
        current_target_y = CFG["ARENA_HEIGHT_M"] / 2
        if self.primary_steering_target_m and self.current_action_name_for_debug == "HoldMidfieldLine":
            current_target_y = self.primary_steering_target_m.y
        ball_y_deadzone = CFG.get("AI_MIDFIELD_HOLD_BALL_Y_DEADZONE_M", 0.25)
        target_y_based_on_ball = (ball.pos_m.y * 0.4) + (CFG["ARENA_HEIGHT_M"] / 2 * 0.6)
        if abs(ball.pos_m.y - self.last_ball_y_for_midfield_hold) > ball_y_deadzone or self.last_ball_y_for_midfield_hold < 0:
            target_y = target_y_based_on_ball
            self.last_ball_y_for_midfield_hold = ball.pos_m.y
        else:
            target_y = current_target_y
        target_y = max(CFG["ARENA_HEIGHT_M"] * 0.25, min(target_y, CFG["ARENA_HEIGHT_M"] * 0.75))
        return self._move_to_position_action(pygame.math.Vector2(target_x, target_y), "HoldMidfieldLine", game_state, "AI_Slowing_RADIUS_POSITION")

    def _build_behavior_tree(self):
        p = self
        if self.player_num == 1:
            self.behavior_tree = Selector(f"ROOT_Attacker_{p}", player=p, children=[
                Sequence("OffensivePlayWithBall", player=p, children=[
                    ConditionNode("HasBall", player=p),
                    Selector("ChooseOffensiveActionWithBall", player=p, children=[
                        Sequence("EscapeOwnThird_Attacker", player=p, children=[
                            ConditionNode("BallInMyDefensiveThird", player=p),
                            Selector("AttackerEscapeChoice", player=p, children=[
                                ActionNode("ClearBall", player=p),
                                ActionNode("DribbleStrategically", player=p)
                            ])
                        ]),
                        Sequence("TryShoot", player=p, children=[ConditionNode("CanShoot", player=p), ActionNode("ShootAtGoal", player=p)]),
                        Sequence("TryPass", player=p, children=[ConditionNode("CanPassToTeammate", player=p), ActionNode("PassToTeammate", player=p)]),
                        ActionNode("DribbleStrategically", player=p)
                    ])
                ]),
                Sequence("WinBall_Attacker", player=p, children=[
                    ConditionNode("IsDesignatedBallWinner", player=p),
                    ConditionNode("HasBall", player=p, negate=True),
                    ConditionNode("TeammateHasBall", player=p, negate=True),
                    ActionNode("GoToBall", player=p)
                ]),
                Sequence("SupportOffense_Attacker", player=p, children=[
                    ConditionNode("HasBall", player=p, negate=True),
                    ConditionNode("IsDesignatedBallWinner", player=p, negate=True),
                    ActionNode("MoveToAttackingSupport", player=p)
                ]),
                ActionNode("GoToBall", player=p)
            ])
        elif self.player_num == 2:
            self.behavior_tree = Selector(f"ROOT_Defender_{p}", player=p, children=[
                Sequence("DefensivePlayWithBall", player=p, children=[
                    ConditionNode("HasBall", player=p),
                    ActionNode("ClearBall", player=p)
                ]),
                Sequence("InterceptHighPriorityThreat_Defender", player=p, children=[
                    ConditionNode("IsDesignatedBallWinner", player=p),
                    ConditionNode("IsMyGoalThreatened", player=p),
                    ConditionNode("HasBall", player=p, negate=True),
                    ActionNode("GoToBall", player=p)
                ]),
                Sequence("CoverSpace_Defender", player=p, children=[
                    ConditionNode("IsDesignatedBallWinner", player=p, negate=True),
                    ConditionNode("HasBall", player=p, negate=True),
                     Selector("WhenToCover", player=p, children=[
                        ConditionNode("IsMyGoalThreatened", player=p),
                        ConditionNode("BallInMyDefensiveThird", player=p),
                     ]),
                    ActionNode("MoveToDefensiveCover", player=p)
                ]),
                Sequence("HoldMidfieldLine_Defender", player=p, children=[
                    ConditionNode("BallInOpponentHalf", player=p),
                    ConditionNode("IsMyGoalThreatened", player=p, negate=True),
                    ActionNode("HoldMidfieldLine", player=p)
                ]),
                ActionNode("MoveToDefensiveCover", player=p)
            ])

    def update_ai(self, dt, ball_obj, all_players_list, is_designated_ball_winner_for_me):
        if not self.is_ai:
            # This method is intended for AI players.
            # Non-AI players are updated via Entity.update() directly in Game.update_game_state.
            return 
        
        if not self.behavior_tree:
            # AI player without a behavior tree can't make decisions, but still apply physics.
            super().update(dt) 
            return

        if self.kick_cooldown_timer > 0: 
            self.kick_cooldown_timer -=1

        # Prepare game state for the behavior tree
        teammates_list = [p for p in all_players_list if p.team == self.team and p is not self]
        opponents_list = [p for p in all_players_list if p.team != self.team]
        game_state_for_bt = {
            'ball': ball_obj, 'teammates': teammates_list, 'opponents': opponents_list,
            'dt': dt, 'is_designated_ball_winner': is_designated_ball_winner_for_me
        }

        # Handle BT resets based on game events
        current_has_ball = self.condition_HasBall(game_state_for_bt)
        just_gained_ball = current_has_ball and not self._last_has_ball_status
        just_lost_ball = not current_has_ball and self._last_has_ball_status
        designation_changed = hasattr(self, '_last_designated_winner_status') and \
                              self._last_designated_winner_status != is_designated_ball_winner_for_me

        if just_gained_ball or just_lost_ball or designation_changed:
            self.dribble_target_m = None 
            self.dribble_target_persists_frames = 0
            self.defensive_cover_target_m = None 
            self.defensive_cover_persists_frames = 0
            log_ai(self, "EVENT", f"StateChange: GainedBall={just_gained_ball}, LostBall={just_lost_ball}, DesigChanged={designation_changed} -> Resetting BT.")
            if self.behavior_tree: # Ensure BT exists before resetting
                self.behavior_tree.reset()

        self._last_has_ball_status = current_has_ball
        self._last_designated_winner_status = is_designated_ball_winner_for_me

        # Logging for AI tick start
        player_focus_check = (CFG.get("DEBUG_AI_PLAYER_FOCUS_NUM",0) in [0, self.player_num])
        if player_focus_check:
            log_ai(self, "TICK_START", f"HasBall: {current_has_ball}, IsWinner: {is_designated_ball_winner_for_me}, PrevAction: {self.current_action_name_for_debug}, Cooldown: {self.kick_cooldown_timer}")

        # Tick the behavior tree to get the primary action/target
        bt_status = "NOT_TICKED" # Default if no BT
        if self.behavior_tree:
            bt_status = self.behavior_tree.tick(game_state_for_bt) 
            # BT tick should set self.primary_steering_target_m and self.current_action_name_for_debug

        # Calculate steering forces based on BT output
        force_objective = pygame.math.Vector2(0,0)
        if self.primary_steering_target_m:
            force_objective = self._arrive(self.primary_steering_target_m, self.slowing_radius_for_primary)
        
        action_name_for_debug_force_log = self.current_action_name_for_debug 

        # --- DEBUG: Check primary_steering_target_m and force_objective for B1 ---
        if self.team == 'B' and self.player_num == 1 and player_focus_check: # Added player_focus_check for conditional printing
            target_pos_str = f"({self.primary_steering_target_m.x:.2f}, {self.primary_steering_target_m.y:.2f})" if self.primary_steering_target_m else "None"
            print(f"DEBUG B1 Pre-Force: Target={target_pos_str}, ForceObjective={force_objective.length():.2f}, Action: {action_name_for_debug_force_log}")

        force_separation = pygame.math.Vector2(0,0)
        if teammates_list: # teammates_list is defined earlier
            force_separation = self._separation(teammates_list, CFG["AI_SEPARATION_DISTANCE"])
        
        current_steering_force = force_objective * CFG["AI_WEIGHT_PRIMARY_OBJECTIVE"]
        current_steering_force += force_separation * CFG["AI_WEIGHT_SEPARATION"]

        # --- DEBUG: Check final current_steering_force for B1 ---
        if self.team == 'B' and self.player_num == 1 and player_focus_check: # Added player_focus_check
            print(f"DEBUG B1 Forces: Obj={force_objective.length():.2f} (w:{CFG['AI_WEIGHT_PRIMARY_OBJECTIVE']}), Sep={force_separation.length():.2f} (w:{CFG['AI_WEIGHT_SEPARATION']}), TotalSteering={current_steering_force.length():.2f}")

        # --- Logic for WebSocket Output (Player B1) AND Local Movement ---
        is_b1_ws_candidate = self.team == 'B' and self.player_num == 1
        
        if is_b1_ws_candidate:
            # B1 will always try to move locally based on its AI.
            # Additionally, if WS is ready, it will send commands.
            self._apply_steering_force(current_steering_force) # Apply force for local sim movement

            current_ws_client_instance = ws_client.ws_game_client 
            ws_client_ready = current_ws_client_instance and current_ws_client_instance.running

            if player_focus_check: # Conditional printing
                print(f"DEBUG B1 WS Check: EligibleForWS={is_b1_ws_candidate}, WSClientReady={ws_client_ready}")
                if not ws_client_ready:
                    if not current_ws_client_instance: 
                        print("DEBUG B1 WS Check: current_ws_client_instance (from ws_client module) is None")
                    elif not current_ws_client_instance.running: 
                        print("DEBUG B1 WS Check: current_ws_client_instance (from ws_client module) is NOT running")
            
            if ws_client_ready: # If client is ready, also send command
                current_time_ns = time.monotonic_ns()
                time_to_send = (current_time_ns - self.last_ws_send_time_ns >= self.ws_send_interval_ns)
                
                if player_focus_check: # Conditional printing
                    print(f"DEBUG B1 WS Check Timing: TimeToSend={time_to_send} (Curr_ns:{current_time_ns}, LastSent_ns:{self.last_ws_send_time_ns}, Interval_ns:{self.ws_send_interval_ns})")

                if time_to_send:
                    if player_focus_check: print(f"DEBUG B1 Send Attempt: SteeringForce L:{current_steering_force.length():.2f}") 
                    sent_command_this_frame = False 

                    if current_steering_force.length_squared() > 1e-9: 
                        normalized_direction = safe_normalize(current_steering_force)
                        api_x = normalized_direction.x
                        api_y = -normalized_direction.y 
                        
                        if player_focus_check: print(f"DEBUG B1 Send Call (Move): current_ws_client_instance.send_joystick_command(userid=1, x={api_x:.2f}, y={api_y:.2f})")
                        current_ws_client_instance.send_joystick_command(userid=1, x=api_x, y=api_y) 
                        sent_command_this_frame = True
                    else:
                        if player_focus_check: print(f"DEBUG B1 Send Call (Stop): current_ws_client_instance.send_joystick_command(userid=1, x=0.0, y=0.0)")
                        current_ws_client_instance.send_joystick_command(userid=1, x=0.0, y=0.0) 
                        sent_command_this_frame = True
                    
                    if sent_command_this_frame:
                        self.last_ws_send_time_ns = current_time_ns
            
            # Log B1's activity
            if CFG.get("DEBUG_LOG_AI_STEERING", False) and player_focus_check:
                log_ai(self, "STEERING_FORCES", f"B1_SIM_AND_WS: SteeringForce L:{current_steering_force.length():.2f}. WS Send (if interval & ready). Acc applied locally.")

        else: 
            # This block handles Player B2 (the other AI player)
            self._apply_steering_force(current_steering_force)
            if CFG.get("DEBUG_LOG_AI_STEERING", False) and player_focus_check:
                 log_ai(self, "STEERING_FORCES", f"ObjectiveF: {force_objective.length():.2f} (w:{CFG['AI_WEIGHT_PRIMARY_OBJECTIVE']}), SeparationF: {force_separation.length():.2f} (w:{CFG['AI_WEIGHT_SEPARATION']}) For {self}")

        # Common logging for all AI players after decisions and force application
        if player_focus_check:
            target_str = f"({self.primary_steering_target_m.x:.2f},{self.primary_steering_target_m.y:.2f})" if self.primary_steering_target_m else "None"
            log_ai(self, "TICK_END", f"NewAction: {self.current_action_name_for_debug}, BT: {bt_status}, Target: {target_str}, Vel: {self.vel_m_s.length():.2f}, Acc: {self.acc_m_s2.length():.2f}")

        super().update(dt) # Apply physics (velocity from acc_m_s2, position) for this AI player
                           # Entity.update() will also reset self.acc_m_s2 to (0,0) at its end.

class Ball(Entity):
    def __init__(self, pos_m):
        super().__init__(pos_m, CFG["BALL_RADIUS_M"], CFG["BALL_MASS"], CFG["COLOR_BALL"])
        self.damping = CFG["BALL_DAMPING"]
    def update(self, dt):
        self.pos_m += self.vel_m_s * dt
        self.vel_m_s *= (1 - self.damping * dt)
        if self.vel_m_s.length_squared() < (0.001 * 0.001):
            self.vel_m_s.update(0,0)

class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((CFG["SCREEN_WIDTH"], CFG["SCREEN_HEIGHT"]))
        pygame.display.set_caption("2v2 Refined BT AI Football Mk4.2 - WS Output for B1")
        self.clock = pygame.time.Clock()
        self.font_score = pygame.font.SysFont("Arial", 36, bold=True)
        self.font_message = pygame.font.SysFont("Arial", 60, bold=True)
        self.font_small_message = pygame.font.SysFont("Arial", 24)

        self.calculate_scales_and_pitch_geometry()
        self.players = []
        self.ball = None
        self.score = {'A': 0, 'B': 0}
        self.game_active = True
        self.last_goal_time_ms = 0
        self.setup_entities_for_kickoff()
        print("Game initialized with Refined Behavior Tree AI Mk4.2 (Full Phases) - WS Output for B1.")
        if _ai_log_file_handle:
             _ai_log_file_handle.write("Game class initialized (Full Phases) - WS Output for B1.\n")
             _ai_log_file_handle.flush()

    def calculate_scales_and_pitch_geometry(self):
        global METERS_TO_PIXELS, PITCH_RECT_PX
        drawable_width_px = CFG["SCREEN_WIDTH"] - 2 * CFG["MARGIN"]
        drawable_height_px = CFG["SCREEN_HEIGHT"] - 2 * CFG["MARGIN"]
        scale_from_width = drawable_width_px / CFG["ARENA_WIDTH_M"]
        scale_from_height = drawable_height_px / CFG["ARENA_HEIGHT_M"]
        METERS_TO_PIXELS = min(scale_from_width, scale_from_height)
        scaled_pitch_width_px = CFG["ARENA_WIDTH_M"] * METERS_TO_PIXELS
        scaled_pitch_height_px = CFG["ARENA_HEIGHT_M"] * METERS_TO_PIXELS
        pitch_x_px = (CFG["SCREEN_WIDTH"] - scaled_pitch_width_px) / 2
        pitch_y_px = (CFG["SCREEN_HEIGHT"] - scaled_pitch_height_px) / 2
        PITCH_RECT_PX = pygame.Rect(pitch_x_px, pitch_y_px, scaled_pitch_width_px, scaled_pitch_height_px)
        self.goal_y_min_m = (CFG["ARENA_HEIGHT_M"] - CFG["GOAL_WIDTH_M"]) / 2
        self.goal_y_max_m = (CFG["ARENA_HEIGHT_M"] + CFG["GOAL_WIDTH_M"]) / 2

    def get_initial_player_positions(self):
        q_w = CFG["ARENA_WIDTH_M"] / 4
        t_h1 = CFG["ARENA_HEIGHT_M"] / 3
        t_h2 = CFG["ARENA_HEIGHT_M"] * 2 / 3
        return [
            (pygame.math.Vector2(q_w, t_h1), 'A', 1),
            (pygame.math.Vector2(q_w, t_h2), 'A', 2),
            (pygame.math.Vector2(CFG["ARENA_WIDTH_M"] - q_w, t_h1), 'B', 1), # AI Player B1 (Attacker)
            (pygame.math.Vector2(CFG["ARENA_WIDTH_M"] - q_w, t_h2), 'B', 2), # AI Player B2 (Defender)
        ]

    def setup_entities_for_kickoff(self):
        self.players.clear()
        initial_player_data = self.get_initial_player_positions()
        for pos_m, team_char, num in initial_player_data:
            self.players.append(Player(pos_m, team_char, num))
        self.ball = Ball(pygame.math.Vector2(CFG["ARENA_WIDTH_M"] / 2, CFG["ARENA_HEIGHT_M"] / 2))
        for p in self.players:
            p.vel_m_s.update(0,0); p.acc_m_s2.update(0,0)
            if p.is_ai and p.behavior_tree:
                p.behavior_tree.reset()
                p.primary_steering_target_m = None
                p._last_has_ball_status = False
                p._last_designated_winner_status = False
                p.current_action_name_for_debug = "Idle_Kickoff"
                p.kick_cooldown_timer = 0
                p.dribble_target_m = None
                p.dribble_target_persists_frames = 0
                p.last_ball_y_for_midfield_hold = -1.0
                p.defensive_cover_target_m = None
                p.defensive_cover_persists_frames = 0
        self.ball.vel_m_s.update(0,0)
        self.game_active = True
        if _ai_log_file_handle:
            _ai_log_file_handle.write("Entities reset for kickoff.\n")
            _ai_log_file_handle.flush()

    def handle_human_input(self):
        keys = pygame.key.get_pressed()
        p1_move_vec = pygame.math.Vector2(0,0)
        if keys[pygame.K_w]: p1_move_vec.y -= 1
        if keys[pygame.K_s]: p1_move_vec.y += 1
        if keys[pygame.K_a]: p1_move_vec.x -= 1
        if keys[pygame.K_d]: p1_move_vec.x += 1
        # Find Player A1 to apply input
        player_a1 = next((p for p in self.players if p.team == 'A' and p.player_num == 1), None)
        if player_a1: player_a1.set_movement_input(p1_move_vec)

        p2_move_vec = pygame.math.Vector2(0,0)
        if keys[pygame.K_UP]: p2_move_vec.y -= 1
        if keys[pygame.K_DOWN]: p2_move_vec.y += 1
        if keys[pygame.K_LEFT]: p2_move_vec.x -= 1
        if keys[pygame.K_RIGHT]: p2_move_vec.x += 1
        # Find Player A2 to apply input
        player_a2 = next((p for p in self.players if p.team == 'A' and p.player_num == 2), None)
        if player_a2: player_a2.set_movement_input(p2_move_vec)


    def resolve_entity_collision(self, e1, e2, restitution):
        diff_vec = e1.pos_m - e2.pos_m
        dist_m_sq = diff_vec.length_squared()
        min_dist_m = e1.radius_m + e2.radius_m
        if dist_m_sq < min_dist_m**2 and dist_m_sq > 1e-9:
            dist_m = math.sqrt(dist_m_sq)
            overlap = min_dist_m - dist_m
            separation_normal = diff_vec / dist_m
            total_inv_mass = (1/e1.mass if e1.mass > 1e-6 else 0) + (1/e2.mass if e2.mass > 1e-6 else 0)
            if total_inv_mass < 1e-9:
                e1_move_factor = 0.5
                e2_move_factor = 0.5
            else:
                e1_move_factor = (1/e1.mass if e1.mass > 1e-6 else 0) / total_inv_mass
                e2_move_factor = (1/e2.mass if e2.mass > 1e-6 else 0) / total_inv_mass
            e1.pos_m += separation_normal * overlap * e1_move_factor
            e2.pos_m -= separation_normal * overlap * e2_move_factor
            relative_vel = e1.vel_m_s - e2.vel_m_s
            vel_along_normal = relative_vel.dot(separation_normal)
            if vel_along_normal < 0:
                impulse_scalar = -(1 + restitution) * vel_along_normal
                if total_inv_mass > 1e-9: impulse_scalar /= total_inv_mass
                else: impulse_scalar = 0
                impulse_vec = impulse_scalar * separation_normal
                if e1.mass > 1e-6 : e1.vel_m_s += impulse_vec / e1.mass
                if e2.mass > 1e-6 : e2.vel_m_s -= impulse_vec / e2.mass

    def update_game_state(self, dt):
        if not self.game_active:
            current_time_ms = pygame.time.get_ticks()
            if current_time_ms - self.last_goal_time_ms > CFG["RESET_DELAY_MS"]:
                if self.score['A'] >= CFG["MAX_SCORE"] or self.score['B'] >= CFG["MAX_SCORE"]:
                    self.score = {'A': 0, 'B': 0}
                    if _ai_log_file_handle:
                        _ai_log_file_handle.write("Max score reached, game fully reset.\n")
                        _ai_log_file_handle.flush()
                self.setup_entities_for_kickoff()
            return

        ai_team_players_b = [p for p in self.players if p.team == 'B' and p.is_ai]
        designated_winner_b = None
        log_ball_winner_decision = CFG.get("DEBUG_LOG_GAME_EVENTS", False)
        log_reason_str = "N/A"

        if len(ai_team_players_b) >= 1:
            if len(ai_team_players_b) == 1:
                designated_winner_b = ai_team_players_b[0]
                if log_ball_winner_decision: log_reason_str = f"Single AI player ({designated_winner_b}) on team B."
            else:
                # Prefer specific player numbers if available, robust fallback otherwise
                p_b_attacker = next((p for p in ai_team_players_b if p.player_num == 1), None)
                p_b_defender = next((p for p in ai_team_players_b if p.player_num == 2), None)

                if not p_b_attacker and p_b_defender: p_b_attacker = p_b_defender # If only defender exists, attacker becomes defender
                elif not p_b_defender and p_b_attacker: p_b_defender = p_b_attacker # If only attacker exists, defender becomes attacker
                elif not p_b_attacker and not p_b_defender: # Fallback if player_nums are not 1 or 2
                    if len(ai_team_players_b) > 0: p_b_attacker = ai_team_players_b[0]
                    if len(ai_team_players_b) > 1: p_b_defender = ai_team_players_b[1]
                    else: p_b_defender = p_b_attacker # Should not happen with 2 AI players

                if p_b_attacker and p_b_defender: # Ensure both are assigned before comparison
                    dist_attacker_ball_sq = p_b_attacker.pos_m.distance_squared_to(self.ball.pos_m)
                    dist_defender_ball_sq = p_b_defender.pos_m.distance_squared_to(self.ball.pos_m)
                    advantage_sq = CFG["AI_BALL_WINNER_PROXIMITY_ADVANTAGE_M"]**2
                    if dist_attacker_ball_sq < dist_defender_ball_sq - advantage_sq:
                        designated_winner_b = p_b_attacker
                        if log_ball_winner_decision: log_reason_str = f"Attacker ({p_b_attacker}) closer (A_dsq:{dist_attacker_ball_sq:.2f} < D_dsq:{dist_defender_ball_sq:.2f} - adv)"
                    elif dist_defender_ball_sq < dist_attacker_ball_sq - advantage_sq:
                        designated_winner_b = p_b_defender
                        if log_ball_winner_decision: log_reason_str = f"Defender ({p_b_defender}) closer (D_dsq:{dist_defender_ball_sq:.2f} < A_dsq:{dist_attacker_ball_sq:.2f} - adv)"
                    else: # Default to attacker or if roughly equidistant
                        designated_winner_b = p_b_attacker
                        if log_ball_winner_decision: log_reason_str = f"Attacker ({p_b_attacker}) default/equidistant (A_dsq:{dist_attacker_ball_sq:.2f}, D_dsq:{dist_defender_ball_sq:.2f})"
                elif p_b_attacker: # Only attacker exists (or was assigned from fallback)
                     designated_winner_b = p_b_attacker
                     if log_ball_winner_decision: log_reason_str = f"Only Attacker ({p_b_attacker}) found for decision."
                elif p_b_defender: # Only defender exists (or was assigned from fallback)
                     designated_winner_b = p_b_defender
                     if log_ball_winner_decision: log_reason_str = f"Only Defender ({p_b_defender}) found for decision."

        if log_ball_winner_decision and _ai_log_file_handle:
            winner_name = str(designated_winner_b) if designated_winner_b else "None"
            _ai_log_file_handle.write(f"GAME_LOG: [BALL_WINNER_DECISION] Winner: {winner_name}. Reason: {log_reason_str}\n")
            _ai_log_file_handle.flush()

        # Update players: AI players get their specific update_ai, others get Entity.update
        for p in self.players:
            if p.is_ai:
                is_player_designated_winner = (p is designated_winner_b)
                p.update_ai(dt, self.ball, self.players, is_player_designated_winner)
            else: # Human players
                p.update(dt) # This calls Entity.update()

        self.ball.update(dt)

        # Player wall collisions
        for p in self.players:
            if p.pos_m.x - p.radius_m < 0: p.pos_m.x = p.radius_m; p.vel_m_s.x *= -0.5
            if p.pos_m.x + p.radius_m > CFG["ARENA_WIDTH_M"]: p.pos_m.x = CFG["ARENA_WIDTH_M"] - p.radius_m; p.vel_m_s.x *= -0.5
            if p.pos_m.y - p.radius_m < 0: p.pos_m.y = p.radius_m; p.vel_m_s.y *= -0.5
            if p.pos_m.y + p.radius_m > CFG["ARENA_HEIGHT_M"]: p.pos_m.y = CFG["ARENA_HEIGHT_M"] - p.radius_m; p.vel_m_s.y *= -0.5

        # Ball wall/goal collisions
        scored_this_frame = False
        goal_scorer_team = None
        if self.ball.pos_m.x - self.ball.radius_m < 0:
            if self.goal_y_min_m < self.ball.pos_m.y < self.goal_y_max_m:
                self.score['B'] += 1; scored_this_frame = True; goal_scorer_team = 'B'
            else:
                self.ball.pos_m.x = self.ball.radius_m
                self.ball.vel_m_s.x *= -CFG["RESTITUTION_BALL_WALL"]
        elif self.ball.pos_m.x + self.ball.radius_m > CFG["ARENA_WIDTH_M"]:
            if self.goal_y_min_m < self.ball.pos_m.y < self.goal_y_max_m:
                self.score['A'] += 1; scored_this_frame = True; goal_scorer_team = 'A'
            else:
                self.ball.pos_m.x = CFG["ARENA_WIDTH_M"] - self.ball.radius_m
                self.ball.vel_m_s.x *= -CFG["RESTITUTION_BALL_WALL"]

        if self.ball.pos_m.y - self.ball.radius_m < 0:
            self.ball.pos_m.y = self.ball.radius_m
            self.ball.vel_m_s.y *= -CFG["RESTITUTION_BALL_WALL"]
        elif self.ball.pos_m.y + self.ball.radius_m > CFG["ARENA_HEIGHT_M"]:
            self.ball.pos_m.y = CFG["ARENA_HEIGHT_M"] - self.ball.radius_m
            self.ball.vel_m_s.y *= -CFG["RESTITUTION_BALL_WALL"]

        if scored_this_frame:
            self.game_active = False
            self.last_goal_time_ms = pygame.time.get_ticks()
            if _ai_log_file_handle:
                 _ai_log_file_handle.write(f"GOAL SCORED! Team {goal_scorer_team}. Score A:{self.score['A']} B:{self.score['B']}\n")
                 _ai_log_file_handle.flush()
            for p_reset in self.players:
                if p_reset.is_ai and p_reset.behavior_tree:
                    p_reset.behavior_tree.reset()
                    p_reset._last_has_ball_status = False
                    p_reset._last_designated_winner_status = False
                    p_reset.current_action_name_for_debug = "Idle_GoalReset"
                    p_reset.kick_cooldown_timer = 0
                    p_reset.dribble_target_m = None
                    p_reset.dribble_target_persists_frames = 0
                    p_reset.last_ball_y_for_midfield_hold = -1.0
                    p_reset.defensive_cover_target_m = None
                    p_reset.defensive_cover_persists_frames = 0

        # Entity-entity collisions
        for i in range(len(self.players)):
            for j in range(i + 1, len(self.players)):
                self.resolve_entity_collision(self.players[i], self.players[j], CFG["RESTITUTION_PLAYER_PLAYER"])
        for p in self.players:
            self.resolve_entity_collision(p, self.ball, CFG["RESTITUTION_PLAYER_BALL"])

    def draw_pitch_and_field(self):
        self.screen.fill(CFG["COLOR_BACKGROUND"])
        pygame.draw.rect(self.screen, CFG["COLOR_PITCH"], PITCH_RECT_PX)
        pygame.draw.rect(self.screen, CFG["COLOR_LINES"], PITCH_RECT_PX, LINE_THICKNESS_PX)
        center_line_start = (PITCH_RECT_PX.centerx, PITCH_RECT_PX.top)
        center_line_end = (PITCH_RECT_PX.centerx, PITCH_RECT_PX.bottom)
        pygame.draw.line(self.screen, CFG["COLOR_LINES"], center_line_start, center_line_end, LINE_THICKNESS_PX)
        center_circle_radius_px = CFG["ARENA_HEIGHT_M"] * 0.15 * METERS_TO_PIXELS
        pygame.draw.circle(self.screen, CFG["COLOR_LINES"], PITCH_RECT_PX.center,
                           center_circle_radius_px, LINE_THICKNESS_PX)
        goal_width_px = CFG["GOAL_WIDTH_M"] * METERS_TO_PIXELS
        goal_top_y_px = PITCH_RECT_PX.centery - goal_width_px / 2
        goal_bottom_y_px = PITCH_RECT_PX.centery + goal_width_px / 2
        pygame.draw.line(self.screen, CFG["COLOR_GOAL"], (PITCH_RECT_PX.left, goal_top_y_px), (PITCH_RECT_PX.left, goal_bottom_y_px), GOAL_LINE_THICKNESS_PX)
        pygame.draw.line(self.screen, CFG["COLOR_GOAL"], (PITCH_RECT_PX.right, goal_top_y_px), (PITCH_RECT_PX.right, goal_bottom_y_px), GOAL_LINE_THICKNESS_PX)
        goal_depth_px = CFG["GOAL_DEPTH_M"] * METERS_TO_PIXELS
        pygame.draw.rect(self.screen, CFG["COLOR_LINES"], (PITCH_RECT_PX.left - goal_depth_px, goal_top_y_px, goal_depth_px, goal_width_px), LINE_THICKNESS_PX // 2)
        pygame.draw.rect(self.screen, CFG["COLOR_LINES"], (PITCH_RECT_PX.right, goal_top_y_px, goal_depth_px, goal_width_px), LINE_THICKNESS_PX // 2)

    def draw_scores_and_messages(self):
        score_text = f"Team A: {self.score['A']}  -  Team B: {self.score['B']}"
        text_surface = self.font_score.render(score_text, True, CFG["COLOR_LINES"])
        text_rect = text_surface.get_rect(center=(CFG["SCREEN_WIDTH"] / 2, CFG["MARGIN"] / 2))
        self.screen.blit(text_surface, text_rect)
        if not self.game_active:
            message = ""
            small_message = ""
            is_game_over = (self.score['A'] >= CFG["MAX_SCORE"] or self.score['B'] >= CFG["MAX_SCORE"])
            if is_game_over:
                winner = "Team A" if self.score['A'] >= CFG["MAX_SCORE"] else "Team B"
                message = f"{winner} WINS!"
                small_message = "Resetting game..."
            else: message = "GOAL!"
            if message:
                msg_surf = self.font_message.render(message, True, (255, 215, 0))
                self.screen.blit(msg_surf, msg_surf.get_rect(center=(CFG["SCREEN_WIDTH"]/2, CFG["SCREEN_HEIGHT"]/2 - 20)))
            if small_message:
                small_msg_surf = self.font_small_message.render(small_message, True, CFG["COLOR_LINES"])
                self.screen.blit(small_msg_surf, small_msg_surf.get_rect(center=(CFG["SCREEN_WIDTH"]/2, CFG["SCREEN_HEIGHT"]/2 + 30)))

    def render_all(self):
        self.draw_pitch_and_field()
        for p in self.players: p.draw(self.screen)
        if self.ball: self.ball.draw(self.screen)
        self.draw_scores_and_messages()
        pygame.display.flip()

    def game_loop(self):
        is_running = True
        loop_count = 0 # Counter for loop iterations

        while is_running:
            loop_count += 1
            # Get raw time for dt before clock.tick potentially caps it
            raw_dt_ms = self.clock.get_rawtime() # Time since last clock.tick() call in ms
            
            # --- DEBUG PRINT FOR LOOP ITERATION ---
            # Print less frequently to avoid spamming, e.g., once per second or every N frames
            if loop_count % CFG["FPS"] == 1 or loop_count < 5 : # Print for first few frames, then once per second
                print(f"Game loop iteration: {loop_count}, Last frame_dt: {raw_dt_ms:.2f}ms")

            dt = min(self.clock.tick(CFG["FPS"]) / 1000.0, 0.1) # Tick the clock and get dt in seconds

            for event in pygame.event.get():
                # --- DEBUG PRINT FOR ALL EVENTS ---
                print(f"Event received: {event}") 

                if event.type == pygame.QUIT:
                    print("!!! QUIT event received! Game will exit.")
                    is_running = False
                if event.type == pygame.KEYDOWN:
                    print(f"--- Keydown event: Key {event.key} ({pygame.key.name(event.key)}) ---")
                    if event.key == pygame.K_ESCAPE:
                        print("!!! ESCAPE key pressed! Game will exit.")
                        is_running = False
                    if event.key == pygame.K_r:
                        print("--- R key pressed: Manual reset initiated. ---")
                        if _ai_log_file_handle: # Ensure handle exists
                            _ai_log_file_handle.write("Manual reset (R pressed).\n")
                            _ai_log_file_handle.flush()
                        self.score = {'A': 0, 'B': 0}
                        self.setup_entities_for_kickoff()

            if not is_running: # If an event caused is_running to be false, break early
                break

            if self.game_active:
                self.handle_human_input()
            
            self.update_game_state(dt)
            self.render_all()

            # Optional: force a small delay if window closes too fast to see anything
            # pygame.time.wait(50) # e.g., 50ms, uncomment ONLY for extreme debugging

        pygame.quit() # Quit Pygame modules
        
        # --- MODIFIED EXIT PRINT ---
        final_exit_message = f"Game exited cleanly after {loop_count} iterations."
        print(final_exit_message)
        if _ai_log_file_handle and not _ai_log_file_handle.closed: # Check if open
            _ai_log_file_handle.write(final_exit_message + "\n")
            _ai_log_file_handle.flush()

if __name__ == '__main__':
    try: del _PLAYER_RADIUS_M_VAL
    except NameError: pass
    try: del _BALL_RADIUS_M_VAL
    except NameError: pass
    try: del _ARENA_WIDTH_M_VAL
    except NameError: pass
    try: del _ARENA_HEIGHT_M_VAL
    except NameError: pass
    try: del _GOAL_WIDTH_M_VAL
    except NameError: pass

    # --- INITIALIZE WEBSOCKET CLIENT ---
    # Global ws_game_client is defined in ws_client.py and imported
    # init_global_ws_client() will create and start it.
    
    try:
        init_global_ws_client() # Initialize and start the WebSocket client thread

        _ai_log_file_handle = open(_AI_LOG_FILE_PATH, "w", encoding="utf-8")
        current_time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        _ai_log_file_handle.write(f"\n--- NEW GAME SESSION STARTING: {current_time_str} ---\n")
        _ai_log_file_handle.flush()

        game_instance = Game()
        game_instance.game_loop()

    except Exception as e:
        print(f"A critical error occurred: {e}")
        if _ai_log_file_handle and not _ai_log_file_handle.closed:
            _ai_log_file_handle.write(f"--- CRITICAL GAME ERROR ---\n")
            _ai_log_file_handle.write(f"Error: {e}\n")
            traceback.print_exc(file=_ai_log_file_handle)
            _ai_log_file_handle.flush()
        # raise # Optionally re-raise to halt execution on critical error

    finally:
        # --- SHUTDOWN WEBSOCKET CLIENT ---
        shutdown_global_ws_client() # Stop the WebSocket client thread gracefully

        if _ai_log_file_handle and not _ai_log_file_handle.closed:
            current_time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            _ai_log_file_handle.write(f"--- GAME SESSION ENDING: {current_time_str} ---\n")
            _ai_log_file_handle.close()
            _ai_log_file_handle = None
            print(f"AI logs have been written to: {_AI_LOG_FILE_PATH}")
        elif not _ai_log_file_handle:
             print(f"Log file was not opened. No AI logs written to file.")