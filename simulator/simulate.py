import json
import os
import time
import random
import threading
from datetime import datetime, timezone
import paho.mqtt.client as mqtt

BROKER = os.environ.get("MQTT_HOST", "localhost")
PORT = 1883
CELL_ID = "cell1"
TOPIC = f"battery/{CELL_ID}/telemetry"
CONTROL_TOPIC = f"battery/{CELL_ID}/control"
CAPACITY_AH = 2.5
R0 = 0.05  # must match twin.py's R0 for the expected-voltage comparison to make sense

# Charge/discharge cycling: discharge until LOW_SOC, then charge until HIGH_SOC, repeat.
DISCHARGE_CURRENT = -2.0
CHARGE_CURRENT = 2.0
LOW_SOC = 20.0
HIGH_SOC = 90.0

MQTT_USERNAME = "twinuser"
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD", "change_me")

connected = threading.Event()
fault_until = 0  # timestamp until which a fault is active


def start_fault(seconds):
    global fault_until
    fault_until = time.time() + seconds
    print(f">>> FAULT INJECTED for {seconds} seconds <<<")


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("Connected to MQTT broker.")
        client.subscribe(CONTROL_TOPIC)
        connected.set()
    else:
        print(f"MQTT connection refused (rc={rc}). Check MQTT_USERNAME / MQTT_PASSWORD.")


def on_message(client, userdata, msg):
    """Handle control commands, for example from the API's fault button."""
    try:
        data = json.loads(msg.payload.decode())
    except (json.JSONDecodeError, UnicodeDecodeError):
        print("Ignoring invalid control message.")
        return
    if not isinstance(data, dict) or data.get("command") != "inject_fault":
        print("Ignoring unknown control command.")
        return
    seconds = data.get("seconds", 10)
    if not isinstance(seconds, (int, float)):
        seconds = 10
    start_fault(max(1, min(30, seconds)))


client = mqtt.Client()
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT)
client.loop_start()

if not connected.wait(timeout=10):
    print("Could not log in to the MQTT broker within 10 seconds. Exiting.")
    client.loop_stop()
    raise SystemExit(1)

soc_estimate = 80.0  # simulator's own rough SoC tracker, used only to steer voltage
voltage = 3.0 + (soc_estimate / 100) * 1.2  # start consistent with the SoC
temperature = 25.0
charging = False  # False = discharging, True = charging


def listen_for_fault():
    while True:
        try:
            input()  # waits for you to press Enter
        except EOFError:
            return  # no keyboard attached (for example inside a container)
        start_fault(10)


threading.Thread(target=listen_for_fault, daemon=True).start()

print(f"Simulator started. Publishing to {TOPIC} every 1 second.")
print("Press Enter (or use the dashboard button) to inject a 10-second fault. Ctrl+C to stop.")

try:
    while True:
        # Decide charge or discharge (with hysteresis so it does not flip-flop)
        if charging and soc_estimate >= HIGH_SOC:
            charging = False
            print(">>> Switching to DISCHARGE <<<")
        elif not charging and soc_estimate <= LOW_SOC:
            charging = True
            print(">>> Switching to CHARGE <<<")

        base_current = CHARGE_CURRENT if charging else DISCHARGE_CURRENT
        current = base_current + random.uniform(-0.1, 0.1)

        soc_estimate += (current * (1 / 3600)) / CAPACITY_AH * 100
        soc_estimate = max(0.0, min(100.0, soc_estimate))

        target_voltage = 3.0 + (soc_estimate / 100) * 1.2 - (current * R0)  # rough SoC-linked target
        voltage += (target_voltage - voltage) * 0.05 + random.uniform(-0.005, 0.005)

        temperature += random.uniform(-0.1, 0.1)

        if time.time() < fault_until:
            temperature += 15.0  # simulate overheating
            voltage -= 0.3       # simulate a voltage drop

        reading = {
            "cell_id": CELL_ID,
            "ts": datetime.now(timezone.utc).isoformat(),
            "voltage": round(voltage, 3),
            "current": round(current, 3),
            "temperature": round(temperature, 2),
        }

        client.publish(TOPIC, json.dumps(reading))
        print(reading)
        time.sleep(1)

except KeyboardInterrupt:
    print("\nSimulator stopped.")
finally:
    client.loop_stop()
    client.disconnect()