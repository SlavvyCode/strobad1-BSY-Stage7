import time
import paho.mqtt.client as mqtt
from consts import *


client = mqtt.Client()
client.connect(BROKER, PORT)

# This runs whenever the bot sends a response back to the 'sensors' topic
def on_message(client, userdata, msg):
    #accept messages taht go lik this : f"{BOT_ID}_RES:
    payload = msg.payload.decode()
    if payload.startswith(f"{BOT_ID}_RES:") or payload.startswith(f"{BOT_ID}_ERR:"):
        print(f"[BOT RESPONSE]: {payload}")


if __name__ == '__main__':
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_message = on_message
    client.connect(BROKER, PORT)
    client.subscribe(TOPIC)
    # loop_start() required over loop_forever() to allow sending commands
    client.loop_start()
    print("Controller is ready. Type a command (e.g., 'id', 'w', 'ping'):")
    try:
        while True:
            cmd = input("> ")
            if cmd.lower() == "exit":
                break
            # Send the command to the broker
            client.publish(TOPIC, f"{BOT_ID}:{cmd}")
            client.publish(TOPIC, cmd)
            # Give bot time to respond
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    client.loop_stop()
    client.disconnect()

