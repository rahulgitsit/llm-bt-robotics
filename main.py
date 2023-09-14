import py_trees.common
from coppeliasim_zmqremoteapi_client import RemoteAPIClient
from actuator import Actuator
from sensors import Sensors
from detector import Detector
from behaviours_refactored import *
from processor_refactored import Processor
from parser import create_tree_from_json
import redis
import json
from state import SaveState

simulation_time = 60 * 60

client = RemoteAPIClient()
sim = client.getObject('sim')
simIK = client.getObject('simIK')

if __name__ == '__main__':
    defaultIdleFps = sim.getInt32Param(sim.intparam_idle_fps)
    sim.setInt32Param(sim.intparam_idle_fps, 0)

    client.setStepping(True)
    sim.startSimulation()

    actuator = Actuator(sim, simIK)
    sensors = Sensors(sim)
    detector = Detector(sim, sensors)
    processor = Processor(sim, actuator, sensors, detector)
    planes = [sim.getObject(f'./plate[{i}]') for i in range(3)]

    tower_plane = sim.getObject('./plate[3]')

    root_test = pt.composites.Sequence(name="Sequence", memory=True)
    state = SaveState()

    redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
    redis_channel = "json_commands"
    redis_subscriber = redis_client.pubsub()
    redis_subscriber.subscribe(redis_channel)
    program_start = True

    try:
        for message in redis_subscriber.listen():
            print("Listening for commands...")
            if message['type'] == 'message':
                response_content = message['data'].decode('utf-8')
                children = create_tree_from_json(response_content, processor=processor, planes=planes,
                                                 tower_plane=tower_plane)
                print(f"Command Received: {children}")

                try:
                    root_test.add_children(children)
                    state.restore_state(children)
                    print("Restored State:", state.print_state())
                except TypeError:
                    print("Your command is invalid. Please give a valid command")

                while root_test.status not in [py_trees.common.Status.FAILURE, py_trees.common.Status.INVALID] or program_start:
                    program_start = False
                    root_test.tick_once()
                    state.update_state(children)
                root_test.status = None
                root_test.remove_all_children()
            print(root_test.status)
            print("Waiting for next command!")

    finally:
        sim.stopSimulation()
        sim.setInt32Param(sim.intparam_idle_fps, defaultIdleFps)

