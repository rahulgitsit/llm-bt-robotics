import cv2
import numpy as np


class Detector:
    def __init__(self, sim, sensors):
        self.sim = sim
        self.sensors = sensors

    def read_cord_colour(self):
        scriptHandle = self.sim.getScript(self.sim.scripttype_childscript, self.sensors.arm_vision_sensor_handle,
                                          'sysCall_sensing')

        self.sim.callScriptFunction('sysCall_init', scriptHandle)
        cords, colours = self.sim.callScriptFunction('sysCall_sensing', scriptHandle)

        return cords, colours

    def find_color(self):
        _, colours = self.read_cord_colour()

        color_ref = {'0': 'red', '1': 'green', '2': 'blue'}
        max_ind = np.argmax(colours[0])
        return color_ref[str(max_ind)]

    def find_color_indices(self, rgb_list, color_name):
        color_indices = []

        color_index = {'red': 0, 'green': 1, 'blue': 2}  # Index of each color component

        for index, rgb in enumerate(rgb_list):
            r, g, b = rgb
            max_component = max(r, g, b)

            if max_component == rgb[color_index[color_name.lower()]]:
                color_indices.append(index)

        return color_indices

    def blob_detect(self, colors=['blue']):
        cords, obj_colours = self.read_cord_colour()

        color_coordinates = {}

        if cords:
            for color in colors:
                indices = self.find_color_indices(obj_colours, color)
                if indices:
                    color_coordinates[color] = [cords[idx] for idx in indices]

        return color_coordinates

    def plane_detect(self, vision_sensor_handle, color='blue'):
        vision_sensor, resX, resY = self.sim.getVisionSensorCharImage(vision_sensor_handle)
        vision_sensor = np.frombuffer(vision_sensor, dtype=np.uint8).reshape(resY, resX, 3)
        vision_sensor = cv2.flip(cv2.cvtColor(vision_sensor, cv2.COLOR_BGR2RGB), 0)

        hsv = cv2.cvtColor(vision_sensor, cv2.COLOR_RGB2HSV)

        color_ranges = {
            "blue": [(0, 70, 50), (10, 255, 255)],
            "red": [(90, 100, 100), (120, 255, 255)],
            "green": [(45, 100, 100), (75, 255, 255)],
        }

        if color not in color_ranges:
            raise ValueError("Invalid color")

        lower_color, upper_color = color_ranges[color]

        # Create a mask for the specified color
        mask = cv2.inRange(hsv, np.array(lower_color), np.array(upper_color))
        result = vision_sensor
        result = cv2.bitwise_and(result, result, mask=mask)
