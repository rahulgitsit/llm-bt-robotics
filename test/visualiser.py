import json
from llm.parser import extract_json_from_string

def print_stack(stack_order, target_loc):
    stack_order = stack_order[::-1]
    stack_size = len(stack_order)
    for i, obj in enumerate(stack_order):
        if (stack_size - i - 1) == 0 and "cube" in target_loc:
            print(f"\t\t{obj} cube <-- base")
        else:
            print(f"\t\t{obj} cube <-- {stack_size - i - 1}")
            print("\t\t-------------------------")

    if target_loc == "random":
        print("\t\tPlaced at random location")
    elif "cube" not in target_loc:
        print(f"\t\t{target_loc} <-- base")
    print("\t\t-------------------------")

def visualise_level_0_1(message, cmd=None):
    stack_order = []
    target_loc = None
    print("Parsing the json command...")
    json_data = extract_json_from_string(message)

    try:
        data = json.loads(json_data)
    except ValueError:
        print("Invalid command. Command expected in JSON")
        return None

    if data["sort the cubes by color"]:
        print("------------------------------------")
        print("cubes will be sorted by their color!")
        print("------------------------------------")
        return
    else:
        if data["place cube"]:
            location = data["location to place"]
            if "cube" in location:
                target_loc = location
                cube_color = location.replace("cube", "").strip()
                stack_order.append(cube_color.lower())
            elif "plane" in location:
                target_loc = location
            elif location == "random" or location == "storage area":
                target_loc = location

        if data["pick up cube"]:
            if isinstance(data["color"], list):
                stack_order.extend(data["color"])
            elif data["color"] == "random":
                stack_order = data["color"]

            if data["place cube"]:
                print("CMD: ", cmd)
                print("#########################")
                print("Stack order is:")
                print_stack(stack_order,target_loc)
            else:
                print("------------------------------------")
                print(f"Picked up {stack_order[0]} cube!")
                print("------------------------------------")






def visualise_level_2(data, cmd=None):
    base = None
    stack_order = []
    print("Parsing the json command...")
    json_data = extract_json_from_string(data)
    try:
        data = json.loads(json_data)
    except ValueError:
        print("Invalid command. Command expected in JSON")
        return None

    target_loc = None

    for item in data:
        print(item)
        if item == "0":
            base = data[item]
            if "plane" in base:
                target_loc = base
            elif "storage" in base:
                target_loc = "storage area"
            elif "cube" in base:
                base_cube_color = base.replace("cube", "").strip()
                target_loc = base
            else:
                raise ValueError(f"Unknown base type: {base}")
        else:
            cube = data[item]
            cube_color = cube.replace("cube", "").strip()
            stack_order.append(cube_color)

    print_stack(stack_order,target_loc)


l1 = '''{
"sort the cubes by color": false,
"pick up cube": true,
"color": ["green","red"],
"place cube": true,
"location to place": "random"
}'''

l2 = '''
{
"0": "var_color2 plane",
"1": "var_color3 cube",
"2": "var_color2 cube",
"3": "var_color 3 cube",
"4": "var_color 1 cube"
}
'''

visualise_level_0_1(l1)
visualise_level_2(l2)
