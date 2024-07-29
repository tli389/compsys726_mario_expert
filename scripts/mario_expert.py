"""
This the primary class for the Mario Expert agent. It contains the logic for the Mario Expert agent to play the game and choose actions.

Your goal is to implement the functions and methods required to enable choose_action to select the best action for the agent to take.

Original Mario Manual: https://www.thegameisafootarcade.com/wp-content/uploads/2017/04/Super-Mario-Land-Game-Manual.pdf
"""

import json
import logging
import random

import cv2
from mario_environment import MarioEnvironment
from pyboy.utils import WindowEvent


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

    def run_action(self, action: int) -> None:
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

    
    def enemy_detect(self,arr):
        enemy_positions = []
        for row_idx, row in enumerate(arr):
            for col_idx, elem in enumerate(row):
                if elem == 15 :
                    enemy_positions.append((row_idx, col_idx))
        return (len(enemy_positions) > 0, enemy_positions)
    
    def tube_detect(self,arr):
        enemy_positions = []
        for row_idx, row in enumerate(arr):
            for col_idx, elem in enumerate(row):
                if elem == 14 :
                    enemy_positions.append((row_idx, col_idx))
        return (len(enemy_positions) > 0, enemy_positions)
    
    def obj_detect(self,arr,ele):
        mario_positions = []
        for row_idx, row in enumerate(arr):
            for col_idx, elem in enumerate(row):
                if elem == ele:
                    mario_positions.append((row_idx, col_idx))
        return mario_positions
        
    def choose_action(self):
        state = self.environment.game_state()
        game_area = self.environment.game_area()
        # Get positions of Mario, tubes, and enemies
        mario_positions = self.obj_detect(game_area, 1)  # Mario represented as 2x2 grid of 1s
        _, enemy_positions = self.enemy_detect(game_area)  # Enemies detected, assuming 15 or 14

        # Define distance thresholds for jumping
        enemy_threshold = 2

        # Rule 1: Check if Mario is close to an enemy and the enemy is to the right
        for mario_pos in mario_positions:
            mario_x, mario_y = mario_pos
            # Check for enemies
            for enemy_pos in enemy_positions:
                enemy_x, enemy_y = enemy_pos
                distance = abs(mario_x - enemy_x) + abs(mario_y - enemy_y)
                if enemy_x > mario_x and distance <= enemy_threshold:
                    return self.environment.valid_actions.index(WindowEvent.PRESS_BUTTON_A)
              
        # Default action if no conditions are met
        return self.environment.valid_actions.index(WindowEvent.PRESS_ARROW_RIGHT)


    def step(self):
        """
        Modify this function as required to implement the Mario Expert agent's logic.

        This is just a very basic example
        """

        # Choose an action - button press or other...
        action = self.choose_action()

        # Run the action on the environment
        self.environment.run_action(action)

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
