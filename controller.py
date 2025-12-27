import paho.mqtt.client as mqtt

BROKER = "147.32.82.209"
PORT = 1883
TOPIC = "sensors"

client = mqtt.Client()
client.connect(BROKER, PORT)

# Requirement 5.1: The controller "asks" if bots are present
print("Sending ping to bots...")
client.publish(TOPIC, "PING_QUERY")

client.disconnect()