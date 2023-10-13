from src.behaviours import *
import json
import re


def extract_json_from_string(data):
    matches = re.findall(r'\{[^{}]*\}', data)

    # Print the last match
    if matches:
        last_match = matches[-1]
        return last_match
    else:
        return None


def create_tree_from_json_level0_1(json_data, processor, planes, storage_plane):
    children = []
    print("Parsing the json command...")
    print(json_data)
    try:
        data = json.loads(json_data)
    except ValueError:
        print("Invalid command. Command expected in JSON")
        return None

    for item in data.get("children", []):
        node_type = item.get("behaviour")
        # node_name = item.get("name")
        node_params = {}

        if "colors" in item:
            node_params["colors"] = item["colors"]
        if "stack_color_order" in item:
            node_params["stack_color_order"] = item["stack_color_order"]
        if "target_loc" in item:
            node_params["target_loc"] = item["target_loc"]
            if node_params["target_loc"] == "temp_storage":
                node_params["target_loc"] = storage_plane

        if node_type:
            if node_type == "FindPlanes":
                children.append(FindPlanes("find_planes", processor, planes, colors=node_params['colors']))
            elif node_type == "SearchCubeOrder":
                children.append(
                    SearchCubeOrder("search_cube", processor, stack_color_order=node_params["stack_color_order"],
                                    stack_loc=node_params["target_loc"]))
            elif node_type == "PickUpCube":
                children.append(PickUpCube("pick_up_cube", processor))
            elif node_type == "PlaceCube":
                children.append(PlaceCube("place_cube", processor, target_loc=node_params["target_loc"]))
            else:
                raise ValueError(f"Unknown node type: {node_type}")

    return children


def parse_json_level0(message, processor, planes, storage_plane):
    children = []
    stack_order = []
    target_loc = None
    print("Parsing the json command...")
    json_data = extract_json_from_string(message)

    try:
        data = json.loads(json_data)
        print(data)
    except ValueError:
        print("Invalid command. Command expected in JSON")
        return None

    if data["sort the cubes by color"]:
        find_plane = FindPlanes("find_planes", processor, planes)
        search = SearchCubeOrder("search_cube", processor, stack_color_order="plane_colors", stack_loc="sort_planes")
        pick_up = PickUpCube("pick_up", processor)
        place_cube = PlaceCube("place_cube", processor, target_loc="sort_planes")
        children.extend([find_plane, search, pick_up, place_cube])
        return children
    else:
        if data["place cube"]:
            location = data["location to place"]
            if "cube" in location:
                target_loc = location
                cube_color = location.replace("cube", "").strip()
                stack_order.append(cube_color.lower())
            elif "plane" in location:
                target_loc = location
                plane_color = location.replace("plane", "").strip()
                find_plane = FindPlanes("find_planes", processor, planes, colors=plane_color)
                children.append(find_plane)
            elif location == "random":
                target_loc = location
            elif location == "storage area":
                target_loc = storage_plane
            place_cube = PlaceCube("place_cube", processor, target_loc=target_loc)

        if data["pick up cube"]:
            if isinstance(data["color"], list):
                stack_order.extend(data["color"])
            elif data["color"] == "random":
                stack_order = data["color"]
            search = SearchCubeOrder("search_cube", processor, stack_color_order=stack_order,
                                     stack_loc=target_loc)
            pick_up = PickUpCube("pick_up", processor)

            if data["place cube"]:
                children.extend([search, pick_up, place_cube])
            else:
                children.extend([search, pick_up])
        else:
            children.extend([place_cube])
        print(children)
        return children


def parse_json_level2(data, processor, planes, storage_plane):
    children = []
    base = None
    stack_order = []
    print("Parsing the json command...")
    json_data = extract_json_from_string(data)
    try:
        data = json.loads(json_data)
        print(data)
    except ValueError:
        print("Invalid command. Command expected in JSON")
        return None

    target_loc = None

    for item in data:
        print(item)
        if item == "0":
            base = data[item]
            if "plane" in base:
                plane_color = base.replace("plane", "").strip()
                children.append(FindPlanes("find_planes", processor, planes, colors=plane_color))
                target_loc = plane_color + "_plane"
            elif "storage" in base:
                target_loc = storage_plane
            elif "cube" in base:
                base_cube_color = base.replace("cube", "").strip()
                stack_order.append(base_cube_color)
                target_loc = base_cube_color + "_cube"
            else:
                raise ValueError(f"Unknown base type: {base}")
        else:
            cube = data[item]
            cube_color = cube.replace("cube", "").strip()
            stack_order.append(cube_color)

    search = SearchCubeOrder("search_cube", processor, stack_color_order=stack_order, stack_loc=target_loc)
    pick_up = PickUpCube("pick_up", processor)
    place_cube = PlaceCube("place_cube", processor, target_loc=target_loc)

    children.extend([search, pick_up, place_cube])
    print(children)
    return children

# data = '''{
# "sort the cubes by color": false,
# "pick up cube": true,
# "color": ["green","red"],
# "place cube": true,
# "location to place": "blue cube"
# }'''
#
# children = parse_json_level0(data,1,1,1)
# print(children)
# create_tree_from_json_level2(data, 1, 1, 1)
