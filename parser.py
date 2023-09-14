from behaviours_refactored import *
import json


def create_tree_from_json(json_data, processor, planes, tower_plane):
    children = []
    print("Parsing the json command...")
    try:
        data = json.loads(json_data)
    except ValueError:
        print("Invalid command. Command expected in JSON")
        return None

    for item in data.get("children", []):
        node_type = item.get("behaviour")
        node_name = item.get("name")
        node_params = {}

        if "colors" in item:
            node_params["colors"] = item["colors"]
        if "stack_loc" in item:
            node_params["stack_loc"] = item["stack_loc"]
        if "target_loc" in item:
            node_params["target_loc"] = item["target_loc"]
            if node_params["target_loc"] == "tower_plane":
                node_params["target_loc"] = tower_plane

        if node_type:
            if node_type == "FindPlanes":
                children.append(FindPlanes(node_name, processor, planes, colors=node_params['colors']))
            elif node_type == "SearchObject":
                children.append(SearchObject(node_name, processor, colors=node_params["colors"], stack_loc=node_params["stack_loc"]))
            elif node_type == "PickUpCube":
                children.append(PickUpCube(node_name, processor, colors=node_params["colors"]))
            elif node_type == "PlaceCube":
                children.append(PlaceCube(node_name, processor, target_loc=node_params["target_loc"]))
            else:
                raise ValueError(f"Unknown node type: {node_type}")

    return children

# with open('example_prompts/ex1_make_tower.json', 'r') as json_file:
#     # Read the JSON data from the file
#     json_data = json_file.read()
#
#     # Call the function with the loaded JSON data
#     children = create_tree_from_json(json_data, processor="processor", planes="planes", tower_plane="tower_plane")