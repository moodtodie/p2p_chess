import socket

subnet_lan = '192.168.0'


def get_local_ip():
    try:
        # Get the local IP address associated with the first non-localhost network interface
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        print(f"Error getting local IP: {e}")
        return None


def find_devices_with_port_open(subnet, port):
    try:
        # the local network range (e.g., {subnet}.1 to {subnet}.255)
        network_range = [(f"{subnet}.{i}", port) for i in range(1, 255)]

        open_devices = []

        # Scan the network range for devices with the specified port open
        for ip, port in network_range:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.05)
            result = sock.connect_ex((ip, port))

            # If the port is open, add the IP address to the list
            if result == 0:
                open_devices.append(ip)

            sock.close()

        return open_devices

    except Exception as e:
        print(f"Error scanning network: {e}")
        return []
