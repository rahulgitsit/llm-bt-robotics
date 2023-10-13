# Master Thesis: Integrating LLMs and Behaviour Trees for Enhanced Robotic Decision-Making
Course: Master Degree in Computer Science
Department: [DISIM - Dipartimento di Ingegneria e Scienze dell'Informazione e Matematica](https://www.disim.univaq.it/)
Supervisor: [Dr. Giovanni De Gasperis](https://www.disim.univaq.it/GiovanniDeGasperis/)
Author: Rahul Pankajakshan


## What's this about?:
This thesis aims to achieve a seamless integration of the Language Model (LLM) with a behavior tree control system, specifically designed for a robotic system operating within the CoppeliaSIM environment. The primary goal is to assess the system's efficiency in handling various levels of command complexity when executing pick and place tasks.

## Project Structure

This repository is organized as follows:

- [**evaluation_set**](evaluation_set/): Contains different command sets for level 0, level 1, level 2, and robustness testing.

- [**prompts**](prompts/): Contains all system prompts used in the experiment.

- [**scene**](scene/): Contains the CoppeliaSim scene file along with the robot and its environment.

- [**src**](src/): Contains various source code files categorized as follows:
  - [**actuator**](src/actuator.py): Functions and API calls to handle the inverse-kinematics and robot's movement
  - [**sensor**](src/sensors.py): Function and API calls to deal with camera and proximity sensor
  - [**detector**](src/detector.py): API calls and helper functions for image processing
  - [**behaviour**](src/behaviour.py): Behaviours and its definition
  - [**processor**](src/processor.py): Processor-related source files.
  - [**state**](src/state.py): State management for the robot and it's environment
