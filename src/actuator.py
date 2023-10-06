import math
import random


class Actuator:
    """
        The actuator controller for the robotic arm with inverse kinematics (IK) capabilities.

        Attributes:
            vel_f (float): The velocity factor for IK calculations.
            accel (float): The acceleration value for IK calculations.
            jerk (float): The jerk value for IK calculations.
            max_vel (list): A list of maximum joint velocities for the robotic arm.
            max_accel (list): A list of maximum joint accelerations for the robotic arm.
            max_jerk (list): A list of maximum joint jerks for the robotic arm.
            metric (list): A list of metrics used in IK calculations.
            in_position (bool): A flag indicating whether the tip of the arm is in the desired position.

        Methods:
            __init__(self, sim, sim_ik):
                Initializes an instance of the Actuator class.

            ik_mov_callback(self, pose, vel, accel, handles):
                Callback function for IK-based movement.

            move_to_pose(self, target_pose):
                Moves the robotic arm to a specified target pose using inverse kinematics.

            place_object(self, destination, tower_size):
                Places an object at a specified destination and tower size.

            pickup_object(self, sensor):
                Picks up an object using a proximity sensor and activates the suction pad.

            move_to_target(self, target_pos=None):
                Moves the robotic arm to a specified target position or a random position within a defined range.
        """

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
    attached = False

    def __init__(self, sim, sim_ik):
        """
            Initializes an instance of the Actuator class.

            Args:
                sim: The simulation environment.
                sim_ik: The inverse kinematics solver for the robotic arm.
        """
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
        """
           Callback function for IK-based movement.

           Args:
               pose: The target pose for the robotic arm.
           Returns:
               None
       """
        self.sim.setObjectPose(self.sim_target, self.sim_base, pose)
        self.sim_ik.handleGroup(self.ik_env, self.ik_group_undamped, {"syncWorlds": True, "allowError": True})

    def move_to_pose(self, target_pose):
        """
           Moves the robotic arm to a specified target pose using inverse kinematics.

           Args:
               target_pose: The target pose to reach.

           Returns:
               None
       """
        current_pose = self.sim.getObjectPose(self.sim_tip, self.sim_base)
        self.sim.setObjectPose(self.sim_target, self.sim_base, current_pose)
        self.sim.moveToPose(-1, current_pose, self.max_vel, self.max_accel, self.max_jerk, target_pose,
                            self.ik_mov_callback, None, self.metric)

    def place_object(self, destination, tower_size):
        """
           Places an object at a specified destination with a specified tower size.

           Args:
               destination: The destination pose for placing the object.
               tower_size: The size of the tower.

           Returns:
               None
       """
        dest = destination.copy()
        dest[2] = 0.6
        print(f"Actuator: placing at {dest}")
        self.move_to_pose(dest)
        dest[2] = 0.083 * tower_size
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
        """
            Picks up an object using a proximity sensor and activates the suction pad.

            Args:
                sensor: sensor class object.

            Returns:
                bool: True if the object is successfully picked up, False otherwise.
        """
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
        """
            Moves the robotic arm to a specified target position or a random position within a defined range.

            Args:
                target_pos: The target position to move to (optional).

            Returns:
                list or None: The target position if successfully reached, None otherwise.
        """

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
