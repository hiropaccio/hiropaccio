"""
aiboo PC monitor - sends stats to Home Assistant via MQTT
========================================================
Install once in PowerShell (Admin):
  pip install psutil pynvml paho-mqtt

Run:
  python aiboo_monitor.py

Auto-start at login (PowerShell Admin):
  $action  = New-ScheduledTaskAction -Execute "python" -Argument "C:\\aiboo_monitor.py"
  $trigger = New-ScheduledTaskTrigger -AtLogOn
  $settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit 0
  Register-ScheduledTask -TaskName "aiboo_monitor" -Action $action -Trigger $trigger -Settings $settings -RunLevel Highest
"""
import json
import socket
import time
import psutil
import paho.mqtt.client as mqtt
import pynvml

MQTT_HOST = "192.168.0.117"   # Raspberry Pi IP
MQTT_PORT = 1883
DEVICE    = "aiboo"
INTERVAL  = 10                # seconds between updates
LOCK_PORT = 47200             # single-instance guard; any unused local port

BASE         = f"homeassistant/sensor/{DEVICE}"
AVAIL_TOPIC  = f"{BASE}/availability"
DEVICE_INFO  = {
    "identifiers": f"custom-{DEVICE}",
    "name": DEVICE,
    "model": "Windows 11 / RTX 5060",
    "manufacturer": "Honome"
}

SENSORS = [
    # (sensor_id,    friendly_name,        unit,  icon,                    device_class)
    ("cpuload",    "CPU 負荷",             "%",   "mdi:cpu-64-bit",        None),
    ("ramload",    "RAM 使用率",           "%",   "mdi:memory",            None),
    ("gpuload",    "GPU 負荷",             "%",   "mdi:expansion-card",    None),
    ("gputemp",    "GPU 温度",             "°C",  "mdi:thermometer",       "temperature"),
    ("gpumemused", "VRAM 使用",            "MiB", "mdi:expansion-card",    None),
    ("gpupower",   "GPU 電力",             "W",   "mdi:lightning-bolt",    "power"),
    ("gpufan",     "GPU ファン",           "RPM", "mdi:fan",               None),
]


def publish_discovery(client):
    for sid, name, unit, icon, dev_class in SENSORS:
        cfg = {
            "unique_id":           f"{DEVICE}_{sid}",
            "name":                f"{DEVICE}_{sid}",
            "state_topic":         f"{BASE}/{DEVICE}_{sid}/state",
            "availability_topic":  AVAIL_TOPIC,
            "unit_of_measurement": unit,
            "icon":                icon,
            "device":              DEVICE_INFO,
        }
        if dev_class:
            cfg["device_class"] = dev_class
        client.publish(f"{BASE}/{DEVICE}_{sid}/config", json.dumps(cfg), retain=True)


def pub(client, sid, value):
    client.publish(f"{BASE}/{DEVICE}_{sid}/state", str(value))


def main():
    # Single-instance guard: a second copy (extra logon, manual run alongside
    # the scheduled task) exits instead of piling up python processes.
    lock = socket.socket()
    try:
        lock.bind(("127.0.0.1", LOCK_PORT))
    except OSError:
        print("aiboo_monitor is already running, exiting.")
        return

    pynvml.nvmlInit()
    gpu = pynvml.nvmlDeviceGetHandleByIndex(0)
    gpu_name = pynvml.nvmlDeviceGetName(gpu)
    print(f"GPU detected: {gpu_name}")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.will_set(AVAIL_TOPIC, "offline", retain=True)
    # connect_async + loop_start keeps retrying until the broker is reachable
    # (e.g. task fires at logon before the network is up) and auto-reconnects.
    client.connect_async(MQTT_HOST, MQTT_PORT, 60)
    client.loop_start()

    publish_discovery(client)
    client.publish(AVAIL_TOPIC, "online", retain=True)
    print(f"Connecting to MQTT at {MQTT_HOST}:{MQTT_PORT}")
    print(f"Sending stats every {INTERVAL} seconds. Press Ctrl+C to stop.")

    while True:
        # CPU & RAM
        pub(client, "cpuload", round(psutil.cpu_percent(interval=1), 1))
        pub(client, "ramload", round(psutil.virtual_memory().percent, 1))

        # GPU via NVML (reads directly from NVIDIA driver, no HWiNFO needed).
        # A driver reset/update makes these raise — skip the cycle and retry
        # next interval instead of letting the exception kill the process.
        try:
            util  = pynvml.nvmlDeviceGetUtilizationRates(gpu)
            mem   = pynvml.nvmlDeviceGetMemoryInfo(gpu)
            temp  = pynvml.nvmlDeviceGetTemperature(gpu, pynvml.NVML_TEMPERATURE_GPU)
            power = pynvml.nvmlDeviceGetPowerUsage(gpu) / 1000  # mW → W

            pub(client, "gpuload",    util.gpu)
            pub(client, "gputemp",    temp)
            pub(client, "gpumemused", round(mem.used / 1024 / 1024))
            pub(client, "gpupower",   round(power, 1))

            try:
                pub(client, "gpufan", pynvml.nvmlDeviceGetFanSpeed(gpu))
            except pynvml.NVMLError:
                pass  # some GPU fan configs are not readable via NVML
        except pynvml.NVMLError as err:
            print(f"NVML read failed, skipping this cycle: {err}")

        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
