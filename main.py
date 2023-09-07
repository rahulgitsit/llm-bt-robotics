from coppeliasim_zmqremoteapi_client import RemoteAPIClient
from actuator import Actuator
from sensors import Sensors
from detector import Detector
from behaviours_refactored import *
from processor_refactored import Processor
# from processor import Processor
# from behaviours import *
from parser import create_tree_from_json
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

    # go_to_plane = MoveToPlane('GoToPlane', planes, processor)
    # search_obj1 = SearchObject('SearchObj1', processor)
    # search_obj2 = SearchObject('SearchObj2', processor)
    # pick_and_place = PickAndPlace('PickAndPlace', processor)
    # get_tower_order = GetTowerOrder('GetTowerOrder', processor)
    # make_tower = StackCubes('MakeTower', processor, tower_plane)
    #
    # root = pt.composites.Sequence(name="Sequence", memory=True)
    # root.add_child(go_to_plane)
    # root.add_child(search_obj1)
    # root.add_child(pick_and_place)
    #
    # root2 = pt.composites.Sequence(name="Sequence", memory=True)
    # root2.add_child(get_tower_order)
    # root2.add_child(search_obj2)
    # root2.add_child(make_tower)
    #
    # search_green = SearchObject("searchobject_green", processor, colors="green", store_pos=True)
    # search_red = SearchObject("searchobject_red", processor, colors="red")
    # stack_red = StackCubes("pick_and_place_red", processor)
    # root3 = pt.composites.Sequence(name="pick_red_place_on_green", memory=True)
    # root3.add_children([search_green, search_red, stack_red])
    #
    # root4 = pt.composites.Sequence(name="pick_red_place_on_green", memory=True)
    # search_red = SearchObject("searchobject_red", processor, colors="red")
    # stack_red = StackCubes("pick_and_place_red", processor, place_object=False)
    # root4.add_children([search_red, stack_red])

    root_test = pt.composites.Sequence(name="json_test", memory=True)
    #scenario1: sort cubes by color
    go_to_plane = FindPlanes('FindPlanes', processor, planes)
    search_obj1 = SearchObject('SearchObj1', processor)
    pick_up = PickUpCube('PickUp',processor)
    place_obj = PlaceCube('PlaceCube',processor)

    #scenario2: make a tower of X,Y,Z
    search_obj2 = SearchObject('SearchObj1', processor, colors=["red","blue","green","blue"])
    pick_up = PickUpCube('PickUp',processor, colors=["red","blue","green","blue"])
    place_obj = PlaceCube('PlaceCube',processor)




    root_test.add_children([go_to_plane,search_obj1,pick_up,place_obj])
    # root_test.add_children([search_obj2,pick_up,place_obj])

    # with open('example_prompts/ex3_pickup.json', 'r') as json_file:
    #     json_data = json_file.read()
    #
    #     children = create_tree_from_json(json_data, processor=processor, planes=planes, tower_plane=tower_plane)
    #
    # root_test.add_children(children)

    try:
        while True:
            root_test.tick_once()
    finally:
        sim.stopSimulation()
        sim.setInt32Param(sim.intparam_idle_fps, defaultIdleFps)
