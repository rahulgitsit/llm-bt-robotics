import numpy as np


def find_color_indices(rgb_list, color_name):
    color_indices = []
    color_index = {'red': 0, 'green': 1, 'blue': 2}  # Index of each color component
    for index, rgb in enumerate(rgb_list):
        r, g, b = rgb
        max_component = max(r, g, b)
        if max_component == rgb[color_index[color_name.lower()]]:
            color_indices.append(index)

    return color_indices


class Detector:
    def __init__(self, sim, sensors):
        self.sim = sim
        self.sensors = sensors

    def read_cord_colour(self):
        script_handle = self.sim.getScript(self.sim.scripttype_childscript, self.sensors.arm_vision_sensor_handle,
                                          'sysCall_sensing')
        self.sim.callScriptFunction('sysCall_init', script_handle)
        cords, colours = self.sim.callScriptFunction('sysCall_sensing', script_handle)
        return cords, colours

    def find_color(self):
        _, colours = self.read_cord_colour()
        color_ref = {'0': 'red', '1': 'green', '2': 'blue'}
        max_ind = np.argmax(colours[0])
        return color_ref[str(max_ind)]

    def blob_detect(self, colors=None):
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

