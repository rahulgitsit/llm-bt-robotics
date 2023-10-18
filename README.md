# Master Thesis: Integrating LLMs and Behaviour Trees for Enhanced Robotic Decision-Making
Course: Master Degree in Computer Science <br>
Department: [DISIM - Dipartimento di Ingegneria e Scienze dell'Informazione e Matematica, Università degli studi dell'Aquila](https://www.disim.univaq.it/) <br>
Supervisor: [Dr. Giovanni De Gasperis](https://www.disim.univaq.it/GiovanniDeGasperis) <br>
Author: Rahul Pankajakshan <br>


## Description
This thesis aims to achieve a seamless integration of the Large Language Model (LLM) with a behaviour tree control system, specifically designed for a robotic system operating within the CoppeliaSim environment. The primary goal is to assess the system's efficiency in handling various levels of command complexity when executing pick and place tasks.

A demo of the system's working can be found here: [here](https://rahulgitsit.github.io/profile/demo)

## Project Structure

This repository is organized as follows:

- [**evaluation_set**](evaluation_set/): Contains different command sets for level 0, level 1, level 2, and robustness testing.

- [**prompts**](prompts/): Contains all system prompts used in the experiment.

- [**scene**](scene/): Contains the CoppeliaSim scene file with the ABB IRB 4600-40 robot model and its environment. 

- [**src**](src/): Contains various source code files categorised as follows:
  - [**actuator**](src/actuator.py): Functions and API calls to handle the inverse-kinematics and robot's movement.
  - [**sensor**](src/sensors.py): Function and API calls to deal with camera and proximity sensor.
  - [**detector**](src/detector.py): API calls and helper functions for image processing.
  - [**behaviour**](src/behaviour.py): Behaviours and its definition. The control system of the robot.
  - [**processor**](src/processor.py): Functions to derive execution logic based on user input and perception data.
  - [**state**](src/state.py): State management for the robot and it's environment

## Install

Install all Python (>=3.10) requirements:

    pip imnstall -r requirements.txt

Clone the CoppeliaSim remote API:

    git clone https://github.com/CoppeliaRobotics/zmqRemoteApi

based on the remote API [CoppeliaSim forum post](https://forum.coppeliarobotics.com/viewtopic.php?t=9392)





