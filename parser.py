from behaviours import *
import json


def create_tree_from_json(json_data, processor, planes, tower_plane):
    children = []

    data = json.loads(json_data)

    for item in data.get("children", []):
        node_type = item.get("behaviour")
        node_name = item.get("name")
        node_params = {}

        if "tower_color_order" in item:
            node_params["tower_color_order"] = item["tower_color_order"]
        if "colors" in item:
            node_params["colors"] = item["colors"]
        if "store_pos" in item:
            node_params["store_pos"] = item["store_pos"]
        if "destination_plane" in item:
            node_params["destination_plane"] = item["destination_plane"]
            if node_params["destination_plane"] is not None:
                node_params["destination_plane"] = tower_plane

        if "place_object" in item:
            node_params["place_object"] = item["place_object"]

        if node_type:
            if node_type == "MoveToPlane":
                children.append(MoveToPlane(node_name, processor, planes))
            elif node_type == "SearchObject":
                children.append(SearchObject(node_name, processor, colors=node_params["colors"], store_pos=node_params["store_pos"]))
            elif node_type == "PickAndPlace":
                children.append(PickAndPlace(node_name, processor))
            elif node_type == "GetTowerOrder":
                children.append(GetTowerOrder(node_name, processor,tower_color_order=node_params["tower_color_order"]))
            elif node_type == "StackCubes":
                children.append(StackCubes(node_name, processor, destination_plane=node_params["destination_plane"], place_object=node_params["place_object"]))
            else:
                raise ValueError(f"Unknown node type: {node_type}")

    return children

# with open('example_prompts/ex1_make_tower.json', 'r') as json_file:
#     # Read the JSON data from the file
#     json_data = json_file.read()
#
#     # Call the function with the loaded JSON data
#     children = create_tree_from_json(json_data, processor="processor", planes="planes", tower_plane="tower_plane")