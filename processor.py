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
        self.search_start = sim.getObject('./search_start')
        self.search_end = sim.getObject('./search_end')
        self.search_start_pose = sim.getObjectPose(self.search_start, self.actuators.simBase)
        self.search_end_pose = sim.getObjectPose(self.search_end, self.actuators.simBase)

    def get_plane_cords(self, plate):
        pos = self.sim.getObjectPose(plate, self.actuators.simBase)
        pos[2] = 0.3
        self.actuators.move_to_pose(pos)
        color = self.detectors.find_color()
        # cords = self.sim.getObjectPosition(plate, self.sim.handle_world)
        return color, pos

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

    def search_object(self, search_start_pos, colors,):
        temp = None
        if not self.started:
            self.actuators.move_to_target_pos(search_start_pos)
            print("at start pos")
            self.started = True
            self.last_pos = search_start_pos
        else:
            print("at last pos")
            if self.last_pos[1] > 1.3:
                self.started = False
                self.last_pos = search_start_pos
                return False, False
            temp = self.actuators.move_to_target_pos(self.last_pos)

        cords = self.detectors.blob_detect(colors)  # cords with colours as the key
        print("blobs:", cords.keys())
        if cords:
            color, pos = next(iter(cords.items()))
            print("color, pos:", color, pos)
            self.last_pos = pos[0]
            if temp is not None or self.actuators.move_to_target_pos(pos[0]) is not None:
                return color, pos[0]
        else:
            self.last_pos[1] += self.increment
        return False, False

    def pick_and_place(self, target, color, plane_pos):
        if self.actuators.pickup_object(self.sensors):
            destination = plane_pos[color]
            self.actuators.place_object(destination)

    def build_tower(self, destination_plane, cube_num):
        if self.actuators.pickup_object(self.sensors):
            self.actuators.place_in_order(destination_plane, cube_num)

    def make_tower(self, target, destination_plane, cube_num):
        if self.actuators.pickup(target, self.sensors):
            self.actuators.place_in_order(destination_plane, cube_num)


    def identify_plates(self, plates):
        initial_pos = self.sim.getObjectPose(self.actuators.simTip, self.actuators.simBase)
        positions = dict()
        for plate in plates:
            pos = self.sim.getObjectPose(plate, self.actuators.simBase)
            pos[2] = 0.3
            self.actuators.move_to_pose(pos)
            color = self.detectors.find_color()
            positions[color] = pos
        self.actuators.move_to_pose(initial_pos)
        return positions
