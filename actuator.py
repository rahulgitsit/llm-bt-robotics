import math
import random


class Actuator:
    # for IK
    vel_f = 1
    accel = 20 * math.pi / 180
    jerk = 10 * math.pi / 180
    max_vel = [vel_f * 175 * math.pi / 180, vel_f * 175 * math.pi / 180, vel_f * 175 * math.pi / 180,
               vel_f * 250 * math.pi / 180, vel_f * 250 * math.pi / 180, vel_f * 360 * math.pi / 180]
    max_accel = [accel] * 3
    max_jerk = [jerk] * 3
    metric = [1, 1, 1, 0.1]
    in_position = False
    prev_intermediate_pos = [999, 999, 999]

    attached = False

    def __init__(self, sim, sim_ik):
        self.sim = sim
        self.sim_ik = sim_ik

        self.joint_handles = [sim.getObject('/IRB4600/joint/', {'index': i}) for i in range(6)]
        self.sim_base = sim.getObject('./IRB4600')
        self.search_start_pose = sim.getObjectPose(sim.getObject('./search_start'), self.sim_base)
        self.search_end_pose = sim.getObjectPose(sim.getObject('./search_end'), self.sim_base)

        # Inverse Kinematics
        self.sim_tip = sim.getObject('./IRB4600/suctionPad/tip')
        self.sim_target = sim.getObject('./Target')
        self.ik_env = sim_ik.createEnvironment()
        self.ik_group_undamped = self.sim_ik.createGroup(self.ik_env)
        self.sim_ik.setGroupCalculation(self.ik_env, self.ik_group_undamped, self.sim_ik.method_pseudo_inverse, 0, 10)
        self.sim_ik.addElementFromScene(self.ik_env, self.ik_group_undamped, self.sim_base, self.sim_tip,
                                        self.sim_target,
                                        self.sim_ik.constraint_pose)

        self.ik_group_damped = self.sim_ik.createGroup(self.ik_env)
        self.sim_ik.setGroupCalculation(self.ik_env, self.ik_group_damped, self.sim_ik.method_damped_least_squares, 0.3,
                                        99)
        self.sim_ik.addElementFromScene(self.ik_env, self.ik_group_damped, self.sim_base, self.sim_tip, self.sim_target,
                                        self.sim_ik.constraint_pose)
        # For suction pad
        self.sim.setInt32Signal("activated", 0)

    def ik_mov_callback(self, pose, vel, accel, handles):
        self.sim.setObjectPose(self.sim_target, self.sim_base, pose)
        self.sim_ik.handleGroup(self.ik_env, self.ik_group_undamped, {"syncWorlds": True, "allowError": True})

    def move_to_pose(self, target_pose):
        current_pose = self.sim.getObjectPose(self.sim_tip, self.sim_base)
        self.sim.setObjectPose(self.sim_target, self.sim_base, current_pose)
        self.sim.moveToPose(-1, current_pose, self.max_vel, self.max_accel, self.max_jerk, target_pose,
                            self.ik_mov_callback, None, self.metric)

    def place_object(self, destination, tower_size):
        dest = destination.copy()
        dest[2] = 0.6
        print(f"Actuator: placing at {dest}")
        self.move_to_pose(dest)
        dest[2] = 0.075 * tower_size
        self.move_to_pose(dest)
        self.sim.setInt32Signal('activated', 0)
        print("Actuator: deactivated the suction pad")
        self.attached = False
        self.in_position = False
        dest[2] = 0.6
        dest[1] += 0.4
        self.move_to_pose(dest)
        dest[2] = 0.3
        self.move_to_pose(dest)

    def pickup_object(self, sensor):
        initial_pos = self.sim.getObjectPose(self.sim_tip, self.sim_base)
        counter = 0
        if not self.attached:
            while True:
                initial_pos[2] -= 0.03
                counter += 1
                self.move_to_pose(initial_pos)
                result, distance, _, detected_object_handle, _ = sensor.get_proximity_sensor()
                if result and distance < 0.1:
                    print("Actuator: activated the suction pad")
                    self.sim.setInt32Signal('activated', 1)
                    self.attached = True
                    initial_pos[2] = 0.5
                    self.move_to_pose(initial_pos)
                    return True
        return False

    def move_to_target(self, target_pos=None):

        initial_pos = self.sim.getObjectPose(self.sim_tip, self.sim_base)

        if target_pos is None:
            print("Actuator: No target given. Moving to random position")
            random_x = round(random.uniform(self.search_start_pose[0], self.search_end_pose[0]), 3)
            random_y = round(random.uniform(self.search_start_pose[0], self.search_end_pose[0]), 3)
            target_pos = self.search_start_pose
            target_pos[0] = random_x
            target_pos[1] = random_y
            target_pos[2] = 0.35

        # for testing
        tgt_pos = target_pos.copy()
        tgt_pos[2] = initial_pos[2]
        if tgt_pos[2] < 0.35:
            tgt_pos[2] = 0.35

        self.move_to_pose(tgt_pos)

        if abs(initial_pos[0]) - abs(tgt_pos[0]) < 0.0001 and abs(initial_pos[1]) - abs(tgt_pos[1]) < 0.0001:
            return target_pos
        else:
            return None
