import math
import random
import numpy as np
from time import sleep


class Actuator:
    # for IK
    velF = 1
    accel = 20 * math.pi / 180
    jerk = 10 * math.pi / 180
    max_vel = [velF * 175 * math.pi / 180, velF * 175 * math.pi / 180, velF * 175 * math.pi / 180,
               velF * 250 * math.pi / 180, velF * 250 * math.pi / 180, velF * 360 * math.pi / 180]
    max_accel = [accel] * 3
    max_jerk = [jerk] * 3
    in_position = False
    prev_intermediate_pos = [999, 999, 999]

    # for suction pad
    infiniteStrength = True
    maxPullForce = 3
    maxShearForce = 1
    maxPeelTorque = 0.1

    metric = [1, 1, 1, 0.1]

    attached = False

    def __init__(self, sim, simIK):
        self.sim = sim
        self.simIK = simIK

        self.joint_handles = [sim.getObject('/IRB4600/joint/', {'index': i}) for i in range(6)]
        self.simBase = sim.getObject('./IRB4600')
        self.search_start = sim.getObject('./search_start')
        self.search_end = sim.getObject('./search_end')
        self.search_start_pose = sim.getObjectPose(self.search_start, self.simBase)
        self.search_end_pose = sim.getObjectPose(self.search_end, self.simBase)

        # Inverse Kinematics
        self.simTip = sim.getObject('./IRB4600/suctionPad/tip')
        self.simTarget = sim.getObject('./Target')
        self.ikEnv = simIK.createEnvironment()
        self.ikGroup_undamped = self.simIK.createGroup(self.ikEnv)
        self.simIK.setGroupCalculation(self.ikEnv, self.ikGroup_undamped, self.simIK.method_pseudo_inverse, 0, 10)
        self.simIK.addElementFromScene(self.ikEnv, self.ikGroup_undamped, self.simBase, self.simTip, self.simTarget,
                                       self.simIK.constraint_pose)

        self.ikGroup_damped = self.simIK.createGroup(self.ikEnv)
        self.simIK.setGroupCalculation(self.ikEnv, self.ikGroup_damped, self.simIK.method_damped_least_squares, 0.3, 99)
        self.simIK.addElementFromScene(self.ikEnv, self.ikGroup_damped, self.simBase, self.simTip, self.simTarget,
                                       self.simIK.constraint_pose)
        self.sim.setInt32Signal("activated", 0)

        # suctionPad
        self.b = sim.getObject('./IRB4600/suctionPad')
        self.l = sim.getObject('./IRB4600/suctionPad/LoopClosureDummy1')
        self.l2 = sim.getObject('./IRB4600/suctionPad/LoopClosureDummy2')
        self.suctionPadLink = sim.getObject('./IRB4600/suctionPad/Link')

    def move_to_position(self, ):
        if self.simIK.handleGroup(self.ikEnv, self.ikGroup_undamped,
                                  {"syncWorlds": True}) != self.simIK.result_success:
            self.simIK.handleGroup(self.ikEnv, self.ikGroup_damped, {"syncWorlds": True, "allowError": True})

    def ik_mov_callback(self, pose, vel, accel, handles):
        self.sim.setObjectPose(self.simTarget, self.simBase, pose)
        self.simIK.handleGroup(self.ikEnv, self.ikGroup_undamped, {"syncWorlds": True, "allowError": True})

    def move_to_pose(self, targetPose):
        currentPose = self.sim.getObjectPose(self.simTip, self.simBase)
        self.sim.setObjectPose(self.simTarget, self.simBase, currentPose)
        self.sim.moveToPose(-1, currentPose, self.max_vel, self.max_accel, self.max_jerk, targetPose,
                            self.ik_mov_callback, None, self.metric)

    def place_object(self, destination, tower_size):
        dest = destination.copy()
        dest[2] = 0.6
        print("placing at ", dest)
        self.move_to_pose(dest)
        dest[2] = 0.075 * tower_size
        self.move_to_pose(dest)
        self.sim.setInt32Signal('activated', 0)
        print("deactivated the suction pad")
        self.attached = False
        self.in_position = False
        dest[2] = 0.6
        dest[1] += 0.4
        self.move_to_pose(dest)
        dest[2] = 0.3
        self.move_to_pose(dest)

    def place_in_order(self, target, cube_num=1):
        if isinstance(target,list):
            destination = self.search_start_pose
            destination[0] = target[0]
            destination[1] = target[1]
        else:
            destination = self.sim.getObjectPose(target, self.simBase)
        destination[2] = 0.6
        print("placing at ", destination)
        self.move_to_pose(destination)
        destination[2] = 0.075 * cube_num
        self.move_to_pose(destination)
        self.sim.setInt32Signal('activated', 0)
        print("deactivated the suction pad")
        self.attached = False
        self.in_position = False
        destination[2] = 0.6
        destination[1] = -0.4
        self.move_to_pose(destination)
        destination[2] = 0.3
        self.move_to_pose(destination)


    def pickup_object(self, sensor):
        initial_pos = self.sim.getObjectPose(self.simTip, self.simBase)
        counter=0
        if not self.attached:
            while True:
                initial_pos[2]-=0.03
                print(counter)
                counter+=1
                self.move_to_pose(initial_pos)
                result, distance, _, detectedObjectHandle, _ = sensor.get_proximity_sensor()
                if result and distance < 0.1:
                    print("activated the suction pad")
                    self.sim.setInt32Signal('activated', 1)
                    self.attached = True
                    initial_pos[2]=0.6
                    self.move_to_pose(initial_pos)
                    return True
        return False

    # def pickup.txt(self, target, sensor):
    #     initial_pos = self.sim.getObjectPosition(self.simTip, self.sim.handle_world)
    #     initial_pos = np.array(initial_pos)
    #     target[2] = 0
    #     target = np.array(target)
    #     increments = (target - initial_pos) / 50
    #     intermediate_pos = initial_pos
    #
    #
    #     # go down the z-axis smoothly
    #     if not self.attached:
    #         for i in range(50):
    #             result, distance, _, detectedObjectHandle, _ = sensor.get_proximity_sensor()
    #             # print("proximity:", result, distance, detectedObjectHandle)
    #             if result and distance < 0.1 and not self.attached:
    #                 # self.attach_object(detectedObjectHandle)
    #                 print("activated the suction pad")
    #                 self.sim.setInt32Signal('activated', 1)
    #                 self.attached = True
    #                 return True
    #                 # self.place_object(detectedObjectHandle, destination)
    #
    #             intermediate_pos = intermediate_pos + increments
    #             self.sim.setObjectPosition(self.simTarget, self.sim.handle_world, intermediate_pos.tolist())
    #             self.move_to_position()
    #     return False

    def move_to_target(self, target_pos=None):

        initial_pos = self.sim.getObjectPose(self.simTip, self.simBase)

        if target_pos is None:
            print("No target given. setting random nearby target")
            random_x = round(random.uniform(self.search_start_pose[0], self.search_end_pose[0]), 3)
            random_y = round(random.uniform(self.search_start_pose[0], self.search_end_pose[0]), 3)
            target_pos = self.search_start_pose
            target_pos[0] = random_x
            target_pos[1] = random_y
            target_pos[2] = 0.35

        # for testing
        target_pos[2] = initial_pos[2]
        if target_pos[2] < 0.35:
            target_pos[2] = 0.35

        if target_pos[0] < 1.3:
            target_pos[0] = 1.3

        # print("in position", initial_pos, target_pos)

        self.move_to_pose(target_pos)
        # truth_val = abs(initial_pos[3]) < 5.0e-10 and abs(initial_pos[4]) < 5.0e-10 and abs(initial_pos[5]) < 5.0e-10
        if abs(initial_pos[0]) - abs(target_pos[0]) < 0.0001 and abs(initial_pos[1]) - abs(target_pos[1]) < 0.0001:
            # print("in position", initial_pos, target_pos)
            return target_pos
        else:
            return None

    # def move_to_target_pos(self, target_pos=None):
    #     initial_pos = self.sim.getObjectPosition(self.simTip, self.sim.handle_world)
    #
    #     if target_pos is None:
    #         print("No target given. setting random nearby target")
    #         random_x = round(random.uniform(1, 2), 3)
    #         random_y = round(random.uniform(-0.5, 0.9), 3)
    #         random_target_pos = [random_x, random_y, 0.45]
    #         target_pos = random_target_pos
    #
    #     # for testing
    #     target_pos[2] = initial_pos[2]
    #     if target_pos[2] < 0.45:
    #         target_pos[2] = 0.45
    #
    #     if target_pos[0] < 1.3:
    #         target_pos[0] = 1.3
    #
    #     initial_pos = np.array(initial_pos)
    #     target_pos = np.array(target_pos)
    #     print("target pos to move:", target_pos)
    #     increments = (target_pos - initial_pos) / 100
    #     increments = np.array(increments)
    #     intermediate_pos = initial_pos
    #
    #     if not self.in_position:
    #         for i in range(100):
    #             intermediate_pos = intermediate_pos + increments
    #             self.sim.setObjectPosition(self.simTarget, self.sim.handle_world, intermediate_pos.tolist())
    #             self.move_to_position()
    #             # sleep(0.01)
    #     print("diff sum ", np.sum(np.abs(self.prev_intermediate_pos - intermediate_pos)).item())
    #
    #     if np.sum(np.abs(self.prev_intermediate_pos - intermediate_pos)).item() < 0.03:
    #         self.in_position = True
    #         print("In position")
    #         self.prev_intermediate_pos = [999, 999, 999]
    #         return target_pos
    #
    #     self.prev_intermediate_pos = intermediate_pos
    #
    #     return None

