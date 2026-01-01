## Project Documentation: MQTT C&C System
student username: strobad1
name: Adam Štrobl
course BSY
year: 2025/26

This project implements a stealthy Command and Control (C&C) channel over MQTT, designed to blend into Industrial IoT traffic.

### 1. Requirements

To run this project, you need Python 3.x and the following libraries:

* `paho-mqtt` (for communication)
* `cryptography` (for AES encryption)

You can install these using the included `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 2. How to Run

Both the controller and the bot can be run inside a Docker container or directly in a terminal.

**Step 1: Start the Bot**
On the "infected" machine:

```bash
python bot.py
```

*The bot will subscribe to the `sensors` topic and begin sending periodic heartbeats. These have no purpose other than to throw off the defending system by more faithfully representing the role of a sensor*

**Step 2: Start the Controller**
On your machine:

```bash
python controller.py
```

*The controller will open an interactive prompt. You can type commands like `ls`, `w`, `id`, or use the `testall` macro to run the full requirement suite. You need to wait before the last command is finished to input another.*

---

### 3. Custom C&C Communication Protocol

The protocol is designed to avoid detection by mimicking standard IoT telemetry.

#### Internal Payload Format:
Once decrypted, the command follows a simple space-delimited string format: 
    `[ACTION] [ARGUMENT]`

Responses are prefixed with 
    `CHK:[CURRENT]:[TOTAL]:`
to facilitate reassembly of large data streams.

#### **Stealth Strategy**

* **Traffic Mimicry:** All messages are wrapped in JSON objects using keys like `s_id`, `v_line` (voltage), and `telemetry_data` to look like power grid sensors.
* **Encryption:** Payloads are encrypted using **AES-128-CBC**. Even if the traffic is intercepted, the commands and responses are unreadable.
* **Uniform Packet Size:** The system uses a 512-byte fixed-size buffer. Short messages are padded with random "junk" characters before encryption so that every packet looks identical in size, preventing traffic analysis based on message length.
* **Chunking:** Large files or long command outputs are broken into fragments (`CHK:XXX:XXX:DATA`) and sent with random delays (3-5 seconds) to avoid "burst" patterns that trigger network alarms.
* **Heartbeats:** The bot sends periodic heartbeat messages disguised as telemetry polls to maintain the illusion of a legitimate sensor.
#### **Packet Structure**

| Field | Description |
| --- | --- |
| `s_id` | Secret Identifier (`GW-MASTER-01` or `SNSR-UNIT-77`) |
| `type` | Disguised as `telemetry_poll` (command) or `telemetry_data` (response) |
| `data` | Base64 encoded string containing the IV + AES-encrypted payload |

---

### 4. Bot Capabilities

The bot supports all the mandatory functions:

1. **Announcement:** Returns bot status when prompted.
2. **User Listing:** Executes `w` to show logged-in users.
3. **Directory Listing:** Executes `ls [dir]` on the host.
4. **Identity:** Returns the output of the `id` command.
5. **Exfiltration:** Reads a local file, encodes it in Base64, and transfers it in chunks to the controller.
6. **Binary Execution:** Can change permissions (`chmod +x`) and execute arbitrary binaries.

Besides these, the bot can also execute any other command sent by the controller.

List of commands supported by the bot which may be required for testing:
- 'botStatus' : Announce bot status
- 'w' : List logged-in users
- 'ls' : List directory contents
- 'ls [directoryPath]' : List directory contents
- 'id' : Show user identity
- 'get [filePath]' : Move a file from bot to controller and save it locally
- './[binaryFile]' : Execute a binary file - example: 'ps'
- './[otherFileToExecute]' : Execute any other file (example: testFileToExecute.sh in root of project)

### 5. Extra

You may go into the bot.py and controller.py files to enable debug logging for more verbose output during execution.

The variable to alter is 'DEBUG_PRINT' and lies at the top of both files. Set it to 'True' to enable additional debug logging.
