import random
from functools import partial


def distance_squared(x, y):
    return (x[0] - y[0]) ** 2 + (x[1] - y[1]) ** 2


class Processor:

    def __init__(self, sim, actuators, sensors, detectors):
        self.sim = sim
        self.actuators = actuators
        self.sensors = sensors
        self.detectors = detectors

        self._increment = 0.3
        self._last_position = None
        self._started = False
        self._blobs_dict = dict()
        self._search_start_pose = sim.getObjectPose(sim.getObject('./search_start'), self.actuators.sim_base)
        self._search_end_pose = sim.getObjectPose(sim.getObject('./search_end'), self.actuators.sim_base)

    def get_plane_coordinates(self, plate):
        """
        Get the coordinates of a plane and its color.

        Args:
            plate: The object representing the plane.

        Returns:
            color (str): The color of the plane.
            pos_rounded (list): The rounded position coordinates of the plane.
        """
        pos = self.sim.getObjectPose(plate, self.actuators.sim_base)
        temp = pos.copy()
        temp[2] = 0.3
        self.actuators.move_to_pose(temp)
        color = self.detectors.find_color()
        pos_rounded = [round(x, 4) for x in pos]
        return color, pos_rounded

    def search_for_object(self, colors, exclude_pos):
        """
           Search for objects of specific colors.

           Args:
               colors (list): List of colors to search for.
               exclude_pos (list): Coordinates to exclude from search.

           Returns:
               color (str): The color of the detected object.
               pos_rounded (list): The rounded position coordinates of the detected object.
       """
        if not self._started:
            print("Searching at search start position")
            self._started = True
            self._last_position = self._search_start_pose.copy()
        else:
            print("Searching at last known position")
            if self._last_position[1] > self._search_end_pose[1]:
                self._started = False
                return False, False

        temp = self.actuators.move_to_target(self._last_position)

        blobs = self.detectors.blob_detect(colors)  # cords with colours as the key
        # print("Blobs Detected: ", blobs)

        if blobs:
            print(f"Processor: exclude pos: {exclude_pos}")

            color, pos = next(iter(blobs.items()))

            if exclude_pos:
                pos = max(list(blobs.values())[0], key=partial(distance_squared, exclude_pos[:3]))
                pos = [pos]

            self._last_position[0] = pos[0][0]
            self._last_position[1] = pos[0][1]
            self._last_position[2] = pos[0][2]

            if temp is not None or self.actuators.move_to_target(self._last_position) is not None:
                pos_rounded = [round(x, 4) for x in self._last_position]
                return color, pos_rounded
        else:
            self._last_position[1] += self._increment
        return False, False

    def pick_up(self, pos):
        """
           Attempt to pick up an object at a given position.

           Args:
               pos (list): The position coordinates of the object to pick up.

           Returns:
               success (bool): True if the object was successfully picked up; False otherwise.
       """
        pos_copy = pos.copy()
        pos_copy[2] = 0.6
        self.actuators.move_to_target(pos_copy)
        return self.actuators.pickup_object(self.sensors)

    def place_cube(self, pos, tower_size):
        """
           Place a cube at a given position.

           Args:
               pos (list or int): The position coordinates or object ID where the cube should be placed.
               tower_size (int): The size of the cube tower.

           Returns:
               None
       """
        if isinstance(pos, int):
            pos = self.sim.getObjectPose(pos, self.actuators.sim_base)
        self.actuators.place_object(pos, tower_size)

    def random_position_generator(self):
        """
           Generate a random position within the search area.

           Returns:
               random_pos (list): Randomly generated position coordinates.
       """
        random_pos = self._search_start_pose.copy()
        random_pos[0] = random.uniform(self._search_start_pose[0], self._search_end_pose[0])
        random_pos[1] = random.uniform(self._search_start_pose[1], self._search_end_pose[1])
        return random_pos
