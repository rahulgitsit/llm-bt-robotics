from time import sleep


class Processor:

    def __init__(self, sim, actuators, sensors, detectors):
        self.last_pos = None
        self.sim = sim
        self.actuators = actuators
        self.sensors = sensors
        self.detectors = detectors
        self.increment = 0.3
        self.started = False
        self.search_start = sim.getObject('./_search_start')
        self.search_end = sim.getObject('./_search_end')
        self.search_start_pose = sim.getObjectPose(self.search_start, self.actuators.sim_base)
        self.search_end_pose = sim.getObjectPose(self.search_end, self.actuators.sim_base)

    def get_plane_cords(self, plate):
        pos = self.sim.getObjectPose(plate, self.actuators.sim_base)
        pos[2] = 0.3
        self.actuators.move_to_pose(pos)
        color = self.detectors.find_color()
        pos_rounded = [round(x, 4) for x in pos]
        return color, pos_rounded

    def search_for_object(self, colors):
        if not self.started:
            print("at start pos")
            self.started = True
            self.last_pos = self.search_start_pose.copy()
        else:
            print("at last pos")
            if self.last_pos[1] > self.search_end_pose[1]:
                self.started = False
                return False, False

        temp = self.actuators.move_to_target(self.last_pos)

        cords = self.detectors.blob_detect(colors)  # cords with colours as the key
        print("blobs:", cords.keys())
        if cords:
            color, pos = next(iter(cords.items()))
            print("color, pos:", color, pos)
            self.last_pos[0] = pos[0][0]
            self.last_pos[1] = pos[0][1]
            self.last_pos[2] = pos[0][2]

            if temp is not None or self.actuators.move_to_target(self.last_pos) is not None:
                return color, self.last_pos
        else:
            self.last_pos[1] += self.increment
        return False, False

    def pick_and_place(self, color, plane_pos):
        if self.actuators.pickup_object(self.sensors):
            destination = plane_pos[color]
            self.actuators.place_object(destination)

    def build_tower(self, target, cube_num, place_object):
        if self.actuators.pickup_object(self.sensors) and place_object:
            self.actuators.place_in_order(target, cube_num)

    def identify_plates(self, plates):
        initial_pos = self.sim.getObjectPose(self.actuators.sim_tip, self.actuators.sim_base)
        positions = dict()
        for plate in plates:
            pos = self.sim.getObjectPose(plate, self.actuators.sim_base)
            pos[2] = 0.3
            self.actuators.move_to_pose(pos)
            color = self.detectors.find_color()
            positions[color] = pos
        self.actuators.move_to_pose(initial_pos)
        return positions
