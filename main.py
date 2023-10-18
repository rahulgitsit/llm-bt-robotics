import py_trees.common
from coppeliasim_zmqremoteapi_client import RemoteAPIClient
from src.actuator import Actuator
from src.sensors import Sensors
from src.detector import Detector
from src.processor import Processor
from llm.parser import *
import redis
from src.state import SaveState
import sys
sys.path.append("./zmqRemoteApi/clients/python/src")

simulation_time = 60 * 60

client = RemoteAPIClient()
sim = client.getObject('sim')
simIK = client.getObject('simIK')

if __name__ == '__main__':
    # CompeliaSim variables
    defaultIdleFps = sim.getInt32Param(sim.intparam_idle_fps)
    sim.setInt32Param(sim.intparam_idle_fps, 0)
    planes = [sim.getObject(f'./plate[{i}]') for i in range(3)]
    storage_plane= sim.getObject('./plate[3]')
    client.setStepping(True)
    sim.startSimulation()

    # init packages
    actuator = Actuator(sim, simIK)
    sensors = Sensors(sim)
    detector = Detector(sim, sensors)
    processor = Processor(sim, actuator, sensors, detector)

    # init root of the behaviour tree as sequence
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
                #select the parser based on complexity
                if response_content[-2:] == "l0":
                    children = parse_json_level0(response_content[:-2], processor=processor, planes=planes,
                                                              storage_plane=storage_plane)
                else:
                    children = parse_json_level2(response_content[:-2], processor=processor, planes=planes,
                                                 storage_plane=storage_plane)
                try:
                    root_test.add_children(children)
                    state.restore_state(children)
                    print("Restored State:", state.print_state())
                except TypeError:
                    print("Your command is invalid. Please give a valid command")

                while root_test.status not in [py_trees.common.Status.FAILURE,
                                               py_trees.common.Status.INVALID] or program_start:
                    program_start = False
                    root_test.tick_once()
                    state.update_state(children)
                root_test.status = None
                root_test.remove_all_children()
            print("Waiting for next command!")

    finally:
        sim.stopSimulation()
        sim.setInt32Param(sim.intparam_idle_fps, defaultIdleFps)
