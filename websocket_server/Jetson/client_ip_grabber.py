#!/usr/bin/env python3
"""
client_ip_grabber.py - Authored by Daniel Theodore Seibert (https://github.com/whistlingelk/)
Copyright (c) 2025 Daniel Theodore Seibert
Released under the MIT License.

Short description:
  Scans the local Wi-Fi subnet for active IP addresses and writes them to "server_ip_address.txt".

How it works:
  • Identifies the local subnet for a given interface.
  • Executes an nmap ping scan over the subnet.
  • Extracts active IP addresses and saves them to "server_ip_address.txt".
  
Dependencies:
  • nmap – For performing ping scans.
  • ipaddress – For subnet calculations.
  • subprocess, sys – For command execution and error handling.

Functions:
  • get_local_subnet(interface: str) -> str:
      Returns the local subnet in CIDR notation.
  • main() -> None:
      Runs the subnet scan and writes discovered IPs to file.
  
Constants:
  • INTERFACE: str (the network interface to scan)
  • OUTPUT_FILE: str (the file to save discovered IPs)
"""

import subprocess
import sys
import ipaddress

INTERFACE = "wlP1p1s0"  # Network interface name for scanning.
OUTPUT_FILE = "server_ip_address.txt"  # Output file for discovered IP addresses.

def get_local_subnet(interface: str) -> str:
    """Returns the local subnet in CIDR notation for a given interface."""
    cmd = ["ip", "-o", "-f", "inet", "addr", "show", interface]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running {' '.join(cmd)}:\n{e}", file=sys.stderr)
        sys.exit(1)

    ip_cidr = None
    for line in result.stdout.splitlines():
        parts = line.split()
        for p in parts:
            if "/" in p:  # e.g., 172.20.10.2/28
                ip_cidr = p
                break
        if ip_cidr:
            break

    if not ip_cidr:
        print(f"Could not parse IP/mask on interface '{interface}'.", file=sys.stderr)
        sys.exit(1)

    network = ipaddress.ip_network(ip_cidr, strict=False)
    return str(network)  # e.g., "172.20.10.0/28"

def main() -> None:
    """Runs the subnet scan and writes discovered IPs to file."""
    print(f"Determining local subnet on interface '{INTERFACE}'...")
    subnet = get_local_subnet(INTERFACE)
    print(f"Subnet is: {subnet}")

    print(f"Scanning subnet {subnet} with nmap -sn -n...")
    cmd = ["nmap", "-sn", "-n", subnet]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running {' '.join(cmd)}:\n{e}", file=sys.stderr)
        sys.exit(1)

    found_ips = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("Nmap scan report for "):
            parts = line.split()
            if len(parts) >= 5:
                ip = parts[4]  # The IP after "Nmap scan report for"
                found_ips.append(ip)

    if found_ips:
        print("Found candidate IP addresses:")
        for ip in found_ips:
            print(ip)
    else:
        print("No active hosts found.", file=sys.stderr)
        sys.exit(1)

    try:
        with open(OUTPUT_FILE, "w") as f:
            for ip in found_ips:
                f.write(f"{ip}\n")
        print(f"Discovered IP addresses saved to {OUTPUT_FILE}")
    except PermissionError:
        print(f"Error: Permission denied when writing to {OUTPUT_FILE}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()