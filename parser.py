import json

# Define your classes here (MoveToPlane, SearchObject, PickAndPlace, GetTowerOrder, MakeTower)

# Sample JSON input (customize this according to your needs)
json_input = '''
{
    "root": {
        "type": "Sequence",
        "name": "Sequence",
        "memory": true,
        "children": [
            {
                "type": "MoveToPlane",
                "name": "GoToPlane",
                "params": ["planes", "processor"]
            },
            {
                "type": "SearchObject",
                "name": "SearchObj1",
                "params": ["processor"]
            },
            {
                "type": "PickAndPlace",
                "name": "PickAndPlace",
                "params": ["processor"]
            }
        ]
    },
    "root2": {
        "type": "Sequence",
        "name": "Sequence",
        "memory": true,
        "children": [
            {
                "type": "GetTowerOrder",
                "name": "GetTowerOrder",
                "params": ["processor"]
            },
            {
                "type": "SearchObject",
                "name": "SearchObj2",
                "params": ["processor"]
            },
            {
                "type": "MakeTower",
                "name": "MakeTower",
                "params": ["processor", "tower_plane"]
            }
        ]
    }
}
'''

# Define a function to create tree objects from JSON
def create_tree_from_json(json_data, processor, tower_plane):
    tree = {}
    for key, value in json_data.items():
        if isinstance(value, dict):
            node_type = value.get("type")
            node_name = value.get("name")
            node_params = value.get("params", [])
            if node_type:
                if node_type == "MoveToPlane":
                    tree[key] = MoveToPlane(node_name, *node_params)
                elif node_type == "SearchObject":
                    tree[key] = SearchObject(node_name, *node_params)
                elif node_type == "PickAndPlace":
                    tree[key] = PickAndPlace(node_name, *node_params)
                elif node_type == "GetTowerOrder":
                    tree[key] = GetTowerOrder(node_name, *node_params)
                elif node_type == "MakeTower":
                    tree[key] = MakeTower(node_name, *node_params)
                else:
                    raise ValueError(f"Unknown node type: {node_type}")
            else:
                tree[key] = create_tree_from_json(value, processor, tower_plane)
    return tree

# Parse the JSON input
json_data = json.loads(json_input)

# Create the behavioral tree objects
root = create_tree_from_json(json_data["root"], processor, tower_plane)
root2 = create_tree_from_json(json_data["root2"], processor, tower_plane)

# Now you can use 'root' and 'root2' in your behavioral tree logic
