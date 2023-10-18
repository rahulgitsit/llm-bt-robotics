import openai
import redis
import os


openai.api_key = os.environ.get("OPENAI_API_KEY")
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
redis_channel = "json_commands"

check_level_prompt = open("../prompts/check_level_prompt.txt", "r").read()
l0_l1_prompt = open("../prompts/l0_l1_prompt.txt", "r").read()
l2_prompt = open("../prompts/l2_prompt.txt", "r").read()


def request_gpt(prompt, user_message, temp=0, max_tokens=256):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": prompt
            },
            user_message
        ],
        temperature=temp,
        max_tokens=max_tokens,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    return response["choices"][0]["message"]["content"]


while True:
    user_input = input("Enter a command: ")
    user_message = {
        "role": "user",
        "content": f"CMD: {user_input}"
    }

    level = request_gpt(check_level_prompt, user_message)
    print("Command level:", level)
    if level.lower() in ["level 0","level 1"]:
        response = request_gpt(l0_l1_prompt, user_message)
        response += "l0"
    else:
        response = request_gpt(l2_prompt, user_message, temp=0, max_tokens=512)
        response += "l2"

    # Publish the response content to the Redis channel
    redis_client.publish(redis_channel, response)
