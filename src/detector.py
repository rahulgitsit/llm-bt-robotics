import numpy as np


def find_color_indices(rgb_list, color_name):
    """
       Find indices of a specific color component in a list of RGB values.

       Args:
           rgb_list (list of tuple): List of RGB values.
           color_name (str): Name of the color component to find ('red', 'green', or 'blue').

       Returns:
           list: List of indices where the specified color component is the maximum.
       """
    color_indices = []
    color_index = {'red': 0, 'green': 1, 'blue': 2}  # Index of each color component
    for index, rgb in enumerate(rgb_list):
        r, g, b = rgb
        max_component = max(r, g, b)
        if max_component == rgb[color_index[color_name.lower()]]:
            color_indices.append(index)

    return color_indices


class Detector:
    """
        The `Detector` class represents color detection functionality.

        Attributes:
            sim: The simulation environment.
            sensors: List of sensors used for detection.

        Methods:
            __init__(self, sim, sensors):
                Initialises an instance of the Detector class.

            read_cord_colour(self):
                Reads color and coordinate data from Lua child script from Coppelia.

            find_color(self):
                Detects the dominant color from sensor data.

            blob_detect(self, colors=None):
                Detects blobs of specified colors in sensor data.

        """
    def __init__(self, sim, sensors):
        """
           Initialises an instance of the Detector class.

           Args:
               sim: The simulation environment.
               sensors: List of sensors used for detection.
       """
        self.sim = sim
        self.sensors = sensors

    def read_cord_colour(self):
        """
            Reads color and coordinate data from the child script in from Coppelia.

            Returns:
                tuple: A tuple containing coordinates and color data.
        """
        script_handle = self.sim.getScript(self.sim.scripttype_childscript, self.sensors.arm_vision_sensor_handle,
                                          'sysCall_sensing')
        self.sim.callScriptFunction('sysCall_init', script_handle)
        cords, colours = self.sim.callScriptFunction('sysCall_sensing', script_handle)
        return cords, colours

    def find_color(self):
        """
            Detects the dominant color from sensor data.

            Returns:
                str: The detected color ('red', 'green', or 'blue').
        """
        _, colours = self.read_cord_colour()
        color_ref = {'0': 'red', '1': 'green', '2': 'blue'}
        max_ind = np.argmax(colours[0])
        return color_ref[str(max_ind)]

    def blob_detect(self, colors=None):
        """
            Detects blobs of specified colors in sensor data.

            Args:
                colors (list): List of color names to detect blobs of.

            Returns:
                dict: A dictionary containing color names as keys and their respective coordinates as values.
        """
        cords, blob_colors = self.read_cord_colour()
        color_coordinates = {}
        if cords:
            try:
                for color in colors:
                    indices = find_color_indices(blob_colors, color)
                    if indices:
                        color_coordinates[color] = [cords[idx] for idx in indices]
                return color_coordinates
            except ValueError:
                print("Detector: Colors cannot be None!")

