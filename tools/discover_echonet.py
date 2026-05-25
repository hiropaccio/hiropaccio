#!/usr/bin/env python3
"""
Discover ECHONET Lite devices on the local network.
Run on the Raspberry Pi:  python3 tools/discover_echonet.py

Sends a multicast GET to the ECHONET Lite node profile object
and prints the IP address and supported object classes of every
responding device.  The RC-307A gateway should appear here.
"""

import socket
import struct
import time

ECHONET_MULTICAST = "224.0.23.0"
ECHONET_PORT = 3610
LISTEN_SECONDS = 5

# ECHONET Lite frame: GET node profile (0x0EF0) property 0xD6
# (self node instance list — returns every object the device exposes)
DISCOVERY_FRAME = bytes([
    0x10, 0x81,        # EHD1, EHD2
    0x00, 0x01,        # TID
    0x05, 0xFF, 0x01,  # SEOJ: generic controller, instance 1
    0x0E, 0xF0, 0x01,  # DEOJ: node profile, instance 1
    0x62,              # ESV: GET
    0x01,              # OPC: 1 property
    0xD6, 0x00,        # EPC: 0xD6 (instance list), PDC: 0
])

# Human-readable names for common ECHONET Lite object classes
OBJECT_NAMES = {
    0x0279: "Solar power generation (太陽光発電)",
    0x027D: "Storage battery (蓄電池)",
    0x02A1: "Smart electric energy meter (低圧スマートメータ)",
    0x0288: "Low-voltage smart meter",
    0x05FF: "Controller (コントローラ)",
    0x0EF0: "Node profile (ノードプロファイル)",
    0x0130: "Home air conditioner (エアコン)",
    0x0272: "Fuel cell (燃料電池)",
    0x02A0: "Hybrid water heater (ハイブリッド給湯)",
}


def parse_instance_list(data: bytes) -> list[int]:
    """Parse 0xD6 property value into a list of 2-byte class codes."""
    if len(data) < 1:
        return []
    count = data[0]
    classes = []
    for i in range(count):
        offset = 1 + i * 3
        if offset + 2 > len(data):
            break
        class_code = (data[offset] << 8) | data[offset + 1]
        classes.append(class_code)
    return classes


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.settimeout(LISTEN_SECONDS)

    # Join multicast group
    mreq = struct.pack("4sL", socket.inet_aton(ECHONET_MULTICAST), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    print(f"Sending ECHONET Lite discovery multicast to {ECHONET_MULTICAST}:{ECHONET_PORT}")
    print(f"Listening for {LISTEN_SECONDS} seconds...\n")

    sock.sendto(DISCOVERY_FRAME, (ECHONET_MULTICAST, ECHONET_PORT))

    found = {}
    deadline = time.time() + LISTEN_SECONDS
    while time.time() < deadline:
        try:
            data, addr = sock.recvfrom(1024)
            ip = addr[0]
            if ip in found:
                continue

            # Minimal frame validation
            if len(data) < 14 or data[0] != 0x10:
                continue

            # Extract the response property data (skip 12-byte header + OPC + EPC + PDC)
            # Layout: EHD1 EHD2 TID(2) SEOJ(3) DEOJ(3) ESV OPC [EPC PDC EDT...]
            if len(data) < 14:
                continue

            esv = data[10]
            opc = data[11]
            if opc < 1:
                continue

            epc = data[12]
            pdc = data[13]
            edt = data[14:14 + pdc] if pdc > 0 else b""

            objects = []
            if epc == 0xD6 and pdc > 0:
                objects = parse_instance_list(edt)

            found[ip] = objects
            print(f"  Device found: {ip}")
            if objects:
                for cls in objects:
                    name = OBJECT_NAMES.get(cls, f"Unknown (0x{cls:04X})")
                    print(f"    0x{cls:04X}  {name}")
            else:
                print("    (could not parse object list — device still reachable)")
            print()

        except socket.timeout:
            break

    sock.close()

    if not found:
        print("No ECHONET Lite devices found.")
        print()
        print("Troubleshooting:")
        print("  1. Check your router's DHCP client list for RC-307A or a Sharp device.")
        print("  2. Make sure the RC-307A is powered on and its LAN cable is connected.")
        print("  3. Ensure this script runs on the same network segment as the RC-307A.")
        print("  4. Some gateways require unicast — check the RC-307A manual for its IP.")
    else:
        print(f"Found {len(found)} device(s).")
        print()
        print("Next step: note the IP address above, then in Home Assistant go to")
        print("  Settings → Integrations → Add Integration → search 'ECHONET Lite'")
        print("  HA will auto-discover the device, or enter the IP manually.")


if __name__ == "__main__":
    main()
