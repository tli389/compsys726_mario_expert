"""
This the primary class for the Mario Expert agent. It contains the logic for the Mario Expert agent to play the game and choose actions.

Your goal is to implement the functions and methods required to enable choose_action to select the best action for the agent to take.

Original Mario Manual: https://www.thegameisafootarcade.com/wp-content/uploads/2017/04/Super-Mario-Land-Game-Manual.pdf
"""

import json
import logging
import random
import numpy as np
import pygame

import cv2
from mario_environment import MarioEnvironment
from pyboy.utils import WindowEvent

from enum import Enum

class JumpType(Enum):
    ENEMY = 'ENEMY'
    GAP = 'GAP'
    WALL = 'WALL'
    NONE = 'NONE'


class MarioController(MarioEnvironment):
    """
    The MarioController class represents a controller for the Mario game environment.

    You can build upon this class all you want to implement your Mario Expert agent.

    Args:
        act_freq (int): The frequency at which actions are performed. Defaults to 10.
        emulation_speed (int): The speed of the game emulation. Defaults to 0.
        headless (bool): Whether to run the game in headless mode. Defaults to False.
    """

    def __init__(
        self,
        act_freq: int = 1,
        emulation_speed: int = 0,
        headless: bool = False,
    ) -> None:
        super().__init__(
            act_freq=act_freq,
            emulation_speed=emulation_speed,
            headless=headless,
        )

        self.act_freq = act_freq

        # Example of valid actions based purely on the buttons you can press
        valid_actions: list[WindowEvent] = [
            WindowEvent.PRESS_ARROW_DOWN,
            WindowEvent.PRESS_ARROW_LEFT,
            WindowEvent.PRESS_ARROW_RIGHT,
            WindowEvent.PRESS_ARROW_UP,
            WindowEvent.PRESS_BUTTON_A,
            WindowEvent.PRESS_BUTTON_B,
        ]

        release_button: list[WindowEvent] = [
            WindowEvent.RELEASE_ARROW_DOWN,
            WindowEvent.RELEASE_ARROW_LEFT,
            WindowEvent.RELEASE_ARROW_RIGHT,
            WindowEvent.RELEASE_ARROW_UP,
            WindowEvent.RELEASE_BUTTON_A,
            WindowEvent.RELEASE_BUTTON_B,
        ]

        self.valid_actions = valid_actions
        self.release_button = release_button

    def run_action(self, action: int, jump_type) -> None:
        """
        This is a very basic example of how this function could be implemented

        As part of this assignment your job is to modify this function to better suit your needs

        You can change the action type to whatever you want or need just remember the base control of the game is pushing buttons
        """
        

        # Simply toggles the buttons being on or off for a duration of act_freq
        self.pyboy.send_input(self.valid_actions[action])

        for _ in range(self.act_freq):
            self.pyboy.tick()

        self.pyboy.send_input(self.release_button[action])
        

    def count_frame(self):
        return self._read_m(0xDA00)

    def is_mario_on_ground(self):
        return self._read_m(0xC20A) == 0x01
    
    def may_mario_jump(self):
        return self.is_mario_on_ground()
    
    def find_mario(self):
        return (self._read_m(0xC202), self._read_m(0xC201)) 
    
    def mario_falling(self):
        return self._read_m(0xC207) == 0x02  # true for falling
    
    def get_goomba_positions(self):
        GOOMBA_TYPE = 0x03  # Replace with the actual type code for Goombas
        OBJECT_TABLE_START = 0xD100  # Example starting address; adjust if necessary
        goomba_positions = []
        for index in range(10):  # Assuming a maximum of 10 objects; adjust if necessary
            # Calculate the address for this object's properties
            object_address = OBJECT_TABLE_START + (index * 0x0B)  # Each object occupies 11 bytes
            
            # Extract object type
            object_type = self._read_m(object_address)  # Read the object type

            if object_type == GOOMBA_TYPE:
                # Extract Y and X position
                y_position = self._read_m(object_address + 2)  # Y position at offset 2
                x_position = self._read_m(object_address + 3)  # X position at offset 3
                # Store Goomba's position
                goomba_positions.append((x_position, y_position))
        return goomba_positions
    
    def get_enemy_positions(self, obj_type):
        OBJECT_TABLE_START = 0xD100  # Example starting address; adjust if necessary
        ENEMY_SIZE = 0x0B  # Each object occupies 11 bytes
        MAX_ENEMIES = 10  # Assuming a maximum of 10 objects; adjust if necessary
        positions = []

        for index in range(MAX_ENEMIES):
            object_address = OBJECT_TABLE_START + (index * ENEMY_SIZE)
            object_type = self._read_m(object_address)

            if object_type == obj_type:
                y_position = self._read_m(object_address + 2)
                x_position = self._read_m(object_address + 3)
                positions.append((x_position, y_position))

        return positions

    def is_enemy_near(self, rect):
        enemy_types = [0x00, 0x04, 0x42]  # Goomba, Nokobon, Bee
        mario_x, mario_y = self.find_mario()

        for obj_type in enemy_types:
            enemy_positions = self.get_enemy_positions(obj_type)
            for (enemy_x, enemy_y) in enemy_positions:
                if rect.collidepoint(enemy_x - mario_x, mario_y - enemy_y):
                    return True

        return False
    
    def is_element_near(self, matrix):
        # Search for the element within the defined rectangle
        for row in range(8, 12 + 1):
            for col in range(5, 14 + 1):
                if matrix[row][col] == 18:
                    return True

        return False
    
    def get_wall_height(self, game_area , lvl = 13):
        y = lvl
        wall_height = 0
        while y > 0 and game_area[y][11] != 0:
            wall_height += 1
            y -= 1
        return wall_height

    def danger_of_gap(self, game_area):
        for y in range(6, len(game_area)): #13
            if game_area[y][11] != 0:
                return False
        return True
    
    def find_mario_ground_level(self, game_area):
        # Find the coordinates of Mario (marked by 1s in the matrix)
        mario_positions = np.argwhere(game_area == 1)

        if mario_positions.size == 0:
            return -1  # Return -1 if Mario is not found in the level scene

        # Get the x-coordinate (column index) of Mario
        mario_x = mario_positions[0][1]

        # Traverse downwards from Mario's row to find the ground level (marked by 10s)
        for row in range(mario_positions[0][0], game_area.shape[0]):
            if game_area[row][mario_x] == 10:
                return row

        return -1  # Return -1 if no ground level is found

    def get_obs(self):
        return self.is_mario_on_ground, self.may_mario_jump, self.find_mario, self.get_goomba_positions, self.mario_falling

    

class MarioExpert:
    """
    The MarioExpert class represents an expert agent for playing the Mario game.

    Edit this class to implement the logic for the Mario Expert agent to play the game.

    Do NOT edit the input parameters for the __init__ method.

    Args:
        results_path (str): The path to save the results and video of the gameplay.
        headless (bool, optional): Whether to run the game in headless mode. Defaults to False.
    """

    def __init__(self, results_path: str, headless=False):
        self.results_path = results_path
        self.environment = MarioController(headless=headless)
        self.video = None
        self.prev_pos = 0
        self.jump_type = JumpType.NONE
        self.jump_count = 0
        self.jump_size = -1
        self.action = [False] * 5
        self.action[1] = True
        self.action[4] = True
        self.stuck = 0

    def set_jump(self, jump_type, size):
        self.jump_type = jump_type
        self.jump_size = size
        self.jump_count = 0

        # Print the new jump type
        # print(f"Jump Type Set To: {self.jump_type}")

    def choose_action(self):
            mario_positions = self.environment.find_mario()
            x_pos = self.environment.game_state()["x_position"]
            mario_speed = x_pos - self.prev_pos

            enemy_positions = self.environment.get_goomba_positions()
            game_area = self.environment.game_area()

            danger_of_enemy = self.environment.is_enemy_near(pygame.Rect(-13, -57, 50, 120)) or self.environment.is_element_near(game_area)
            danger_of_enemy_above = self.environment.is_enemy_near(pygame.Rect(-13, -20, 50, 30))
            danger_of_gap = self.environment.danger_of_gap(game_area)

            #print(danger_of_enemy, danger_of_gap, mario_speed)

            if self.environment.is_mario_on_ground() and self.jump_type != JumpType.NONE:
                self.set_jump(JumpType.NONE, -1)
            elif self.environment.may_mario_jump():
                wall_height = self.environment.get_wall_height(game_area)
                if danger_of_gap : #and mario_speed > 0:
                    self.set_jump(JumpType.GAP, 20 - mario_speed)
                elif mario_speed <= 0 and not danger_of_enemy_above and wall_height > 0:
                    self.set_jump(JumpType.WALL, wall_height + 7 if wall_height >= 2 else wall_height)
                elif danger_of_enemy:
                    self.set_jump(JumpType.ENEMY, 15)

            else:
                self.jump_count += 1

            action_index = self.environment.valid_actions.index(WindowEvent.PRESS_ARROW_RIGHT)
            if self.environment.mario_falling() and ((danger_of_enemy and danger_of_enemy_above) or danger_of_gap): 
                action_index = self.environment.valid_actions.index(WindowEvent.PRESS_ARROW_LEFT)
            elif self.jump_type != JumpType.NONE and self.jump_count < self.jump_size: action_index = self.environment.valid_actions.index(WindowEvent.PRESS_BUTTON_A)
            elif not(self.environment.mario_falling()) and not((danger_of_enemy_above and self.jump_type == JumpType.WALL)): 
                action_index = self.environment.valid_actions.index(WindowEvent.PRESS_ARROW_RIGHT)
                
            self.prev_pos = x_pos
            return action_index


    def step(self):
        """
        Modify this function as required to implement the Mario Expert agent's logic.

        This is just a very basic example
        """

        # Choose an action - button press or other...
        action = self.choose_action()

        # Run the action on the environment
        self.environment.run_action(action, self.jump_type)

    def play(self):
        """
        Do NOT edit this method.
        """
        self.environment.reset()

        frame = self.environment.grab_frame()
        height, width, _ = frame.shape

        self.start_video(f"{self.results_path}/mario_expert.mp4", width, height)

        while not self.environment.get_game_over():
            frame = self.environment.grab_frame()
            self.video.write(frame)

            self.step()

        final_stats = self.environment.game_state()
        logging.info(f"Final Stats: {final_stats}")

        with open(f"{self.results_path}/results.json", "w", encoding="utf-8") as file:
            json.dump(final_stats, file)

        self.stop_video()

    def start_video(self, video_name, width, height, fps=30):
        """
        Do NOT edit this method.
        """
        self.video = cv2.VideoWriter(
            video_name, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height)
        )

    def stop_video(self) -> None:
        """
        Do NOT edit this method.
        """
        self.video.release()