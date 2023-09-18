import openai
import redis

openai.api_key = "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"

# Initialize a Redis client
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

# Define the channel name for publishing
redis_channel = "json_commands"

while True:
    user_input = input("Enter a command: ")
    user_message = {
        "role": "user",
        "content": f"CMD: {user_input}"
    }

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are an intermediary to a robotic system that converts natural language commands to JSON. STRICTLY adhere to the *constraints* no matter what. Only respond with JSON.\n\n*constraints*:\n\n1) The robot's environment contains ONLY cubes and plates. There are cubes and planes of RGB colors and another plane of yellow color, which is the \"tower_plane\".\n2)\"stack_color_order\"  can only take values {\"red\",\"green\",\"blue\"} \"random\", \"plane_colors\". If given as codes \"R\",\"G\",B\", it must be expanded to \"red\", \"green\",\"blue\". These are colors of the cube alone NOT the plane\n3) \"\"colors\"  can take the values {\"red\",\"green\",\"blue\"}  \"plane_colors\". \n4) A maximum of one \"SearchCubeOrder\", one \"PickUpCube\", one \"PlaceCube\" and one \"FindPlanes\" is allowed per \"children\".\n5) \"target_loc\" and stack_loc can be \"tower_plane,\" or \"random\" or \"{var_color}_plane\" or \"{var_color}_cube\"or \"sort_planes\" or null .\n6) \"If the command is ambiguous or unclear, respond with: \"Error. Instruction unclear. Please provide more details.\"\n\n\nYour first task is to correctly identify the colour order of the cube stack. Think about this step by step and use in \"stack_color_order\".\nFor example: \n1) {var_color1} cube on top of {var_color2} cube => stack_color_order {var_color2}{var_color1}\n2) 2 {var_color1} cubes on {var_color2} cube and {var_color3} finally => stack_color_order {var_color2}{var_color1}{var_color1}{var_color3}\n\nYour second task is to map it based on the following examples:\n\nCMD: Place {var_color1} cube on top of {var_color2} cube. Then place a {var_color3} cube and finally a {var_color4} cube.\n{\n  \"type\": \"sequence\",\n  \"name\": \"stack_cube\",\n  \"children\": [\n    {\n      \"behaviour\": \"SearchCubeOrder\",\n      \"stack_color_order\": [\"{var_color2}\", \"{var_color1}\", \"{var_color3}\", \"{var_color4}\"],\n      \"stack_loc\": \"{var_color2}_cube\"\n    },\n    {\n      \"behaviour\": \"PickUpCube\"\n    },\n    {\n      \"behaviour\": \"PlaceCube\",\n      \"target_loc\": \"{var_color2}_cube\"\n    }\n  ]\n}\n\nCMD: Make a stack/tower of {var_color1}{var_color2}{var_color3}{var_color4} on the allotted plane.\n{\n  \"type\": \"sequence\",\n  \"name\": \"stack_cube\",\n  \"children\": [\n    {\n      \"behaviour\": \"SearchCubeOrder\",\n      \"stack_color_order\": [\"{var_color1}\",\"{var_color2}\",\"{var_color3}\",\"{var_color4}\"],\n      \"stack_loc\": \"tower_plane\"\n    },\n    {\n      \"behaviour\": \"PickUpCube\"\n    },\n    {\n      \"behaviour\": \"PlaceCube\",\n      \"target_loc\": \"tower_plane\"\n    }\n  ]\n}\nCMD: Make a stack/tower of {var_color1}, {var_color2}. then add 2 {var_color3} on top of it.\n{\n  \"type\": \"sequence\",\n  \"name\": \"stack_cube\",\n  \"children\": [\n    {\n      \"behaviour\": \"SearchCubeOrder\",\n      \"stack_color_order\": [\"{var_color1}\", \"{var_color2}\", \"{var_color3}\", \"{var_color3}\"],\n      \"stack_loc\": \"{var_color1}_cube\"\n    },\n    {\n      \"behaviour\": \"PickUpCube\"\n    },\n    {\n      \"behaviour\": \"PlaceCube\",\n      \"target_loc\": \"{var_color1}_cube\"\n    }\n  ]\n}\n\nCMD: Pick a  {var_color1} cube and place it on top of {var_color2} cube. Then add  a {var_color3} finally.\n{\n  \"type\": \"sequence\",\n  \"name\": \"stack_cube\",\n  \"children\": [\n    {\n      \"behaviour\": \"SearchCubeOrder\",\n      \"stack_color_order\": [\"{var_color2}\", \"{var_color1}\", \"{var_color3}\"],\n      \"stack_loc\": \"{var_color2}_cube\"\n    },\n    {\n      \"behaviour\": \"PickUpCube\"\n    },\n    {\n      \"behaviour\": \"PlaceCube\",\n      \"target_loc\": \"{var_color2}_cube\"\n    }\n  ]\n}\n\nCMD: Pickup a {var_color1} cube.\n{\n  \"type\": \"sequence\",\n  \"name\": \"pick_up\",\n  \"children\": [\n    {\n      \"behaviour\": \"SearchCubeOrder\",\n      \"stack_color_order\": [\"{var_color1}\"],\n      \"stack_loc\": null\n    },\n    {\n      \"behaviour\": \"PickUpCube\"\n    }\n  ]\n}\n\nCMD: Sort the cubes by color.\n{\n  \"type\": \"sequence\",\n  \"name\": \"sort\",\n  \"children\": [\n    {\n      \"behaviour\": \"FindPlanes\",\n      \"colors\": \"plane_colors\"\n    },\n    {\n      \"behaviour\": \"SearchCubeOrder\",\n      \"stack_color_order\": \"plane_colors\",\n      \"stack_loc\": \"sort_planes\"\n    },\n    {\n      \"behaviour\": \"PickUpCube\"\n    },\n    {\n      \"behaviour\": \"PlaceCube\",\n      \"target_loc\": \"sort_planes\"\n    }\n  ]\n}\nCMD: Place/stack the cubes with the same color together.\n{\n  \"type\": \"sequence\",\n  \"name\": \"sort\",\n  \"children\": [\n    {\n      \"behaviour\": \"FindPlanes\",\n      \"colors\": \"plane_colors\"\n    },\n    {\n      \"behaviour\": \"SearchCubeOrder\",\n      \"stack_color_order\": \"plane_colors\",\n      \"stack_loc\": \"sort_planes\"\n    },\n    {\n      \"behaviour\": \"PickUpCube\"\n    },\n    {\n      \"behaviour\": \"PlaceCube\",\n      \"target_loc\":\"sort_planes\"\n    }\n  ]\n}\nCMD: Place the cube somewhere.\n{\n  \"type\": \"sequence\",\n  \"name\": \"place_cube\",\n  \"children\": [\n    {\n      \"behaviour\": \"PlaceCube\",\n      \"target_loc\": \"random\"\n    }\n  ]\n}\n\nCMD: Place {var_color1} cube please.\n{\n  \"type\": \"sequence\",\n  \"name\": \"place_cube\",\n  \"children\": [\n    {\n      \"behaviour\": \"PlaceCube\",\n      \"target_loc\": null\n    }\n  ]\n}\n\nCMD: Pick a {var_color1} cube and place it on the {var_color2} plane.\n{\n  \"type\": \"sequence\",\n  \"name\": \"place_cube\",\n  \"children\": [\n    {\n      \"behaviour\": \"FindPlanes\",\n      \"colors\": \"{var_color2}\"\n    },\n    {\n      \"behaviour\": \"SearchCubeOrder\",\n      \"stack_color_order\": \"[{var_color1}]\",\n      \"stack_loc\": \"{var_color2}_plane\"\n    },\n    {\n      \"behaviour\": \"PickUpCube\"\n    },\n    {\n      \"behaviour\": \"PlaceCube\",\n      \"target_loc\": \"{var_color2}_plane\"\n    }\n  ]\n}\n\nCMD: I need you to find a {var_color1} cube and place it on the {var_color2} plane.\n{\n  \"type\": \"sequence\",\n  \"name\": \"place_cube\",\n  \"children\": [\n    {\n      \"behaviour\": \"FindPlanes\",\n      \"colors\": \"{var_color2}\"\n    },\n    {\n      \"behaviour\": \"SearchCubeOrder\",\n      \"stack_color_order\": [\"{var_color1}\"],\n      \"stack_loc\": \"{var_color2}_plane\"\n    },\n    {\n      \"behaviour\": \"PickUpCube\"\n    },\n    {\n      \"behaviour\": \"PlaceCube\",\n      \"target_loc\": \"{var_color2}_plane\"\n    }\n  ]\n}"
            },
            user_message
        ],
        temperature=0,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    # Get the response content
    response_content = response["choices"][0]["message"]["content"]
    print("Executing")
    # Publish the response content to the Redis channel
    redis_client.publish(redis_channel, response_content)
