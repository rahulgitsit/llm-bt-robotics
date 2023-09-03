from coppeliasim_zmqremoteapi_client import RemoteAPIClient
from actuator import Actuator
from sensors import Sensors
from detector import Detector
from processor import Processor
from behaviours import *
from time import sleep


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

    # black_board = BlackBoard()
    go_to_plane = MoveToPlane('GoToPlane', planes, processor)
    search_obj1 = SearchObject('SearchObj1', processor)
    search_obj2 = SearchObject('SearchObj2', processor)
    pick_and_place = PickAndPlace('PickAndPlace', processor)
    get_tower_order = GetTowerOrder('GetTowerOrder', processor)
    make_tower = MakeTower('MakeTower', processor, tower_plane)

    root = pt.composites.Sequence(name="Sequence", memory=True)
    root.add_child(go_to_plane)
    root.add_child(search_obj1)
    root.add_child(pick_and_place)

    root2 = pt.composites.Sequence(name="Sequence", memory=True)
    root2.add_child(get_tower_order)
    root2.add_child(search_obj2)
    root2.add_child(make_tower)

    # root2.setup_with_descendants()

    choice = int(input("What do you want to do?\n 1. Sort by colour \n 2. Make a tower \n"))
    while True:
        if choice == 1:
            root.tick_once()
        elif choice == 2:
            root2.tick_once()
    # positions = processor.identify_plates(plates)

    # while sim.getSimulationTime() < simulation_time:
    #     color = list(positions.keys())
    #     print(color)
    #     cords = detector.blob_detect(color=color[0])
    #     if len(cords) > 0:
    #         print(f"{len(cords)} blob(s) detected!")
    #         if actuator.move_to_target_pos(cords[0]):
    #             actuator.pickup(cords[0], sensors, positions[color[0]])
    #             actuator.move_to_target_pos(target_pos=None)
    #     else:
    #         actuator.move_to_target_pos(target_pos=None)
    #         print("New random target pos")
    #     client.step()

    sim.stopSimulation()
    sim.setInt32Param(sim.intparam_idle_fps, defaultIdleFps)
