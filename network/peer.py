import argparse
import os
import socket
import threading
import time

# from network.service import find_devices_with_port_open, get_local_ip
from service import find_devices_with_port_open, get_local_ip


class Peer:
    def __init__(self, host, port):  # DEBUG
        self.host = host  # DEBUG
        # self.host = get_local_ip()
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.addresses = []
        self.active_connection = None
        self.connection_address = None

        threading.Thread(target=self.find_connections, args=()).start()

    def find_connections(self):
        while True:
            if self.active_connection is None:
                # subnet = '192.168.0' # LAN
                subnet = '127.0.0'  # Debug
                # self.find_free_connections(find_devices_with_port_open(subnet, self.port))
                addresses = find_devices_with_port_open(subnet, self.port)
                self.addresses.clear()
                self.addresses = addresses
                try:
                    self.addresses.remove(self.host)
                except ValueError:
                    pass

    def find_free_connections(self, addresses):
        free_addresses = []

        if self.active_connection is None:
            for address in addresses:
                self.connect(address, self.port)
                time.sleep(0.5)
                if self.active_connection is not None:
                    free_addresses.append(address)
                    self.disconnect(self.active_connection, address)

        self.addresses = free_addresses

    def connect(self, peer_host, peer_port):
        try:
            connection = socket.create_connection((peer_host, peer_port))

            if self.active_connection is not None:
                self.disconnect(self.active_connection, self.connection_address)

            self.active_connection = connection
            self.connection_address = f'({peer_host}:{peer_port})'

            print(f"[{self.host:}:{self.port}] Connected to {peer_host}:{peer_port}")
            time.sleep(1)
            threading.Thread(target=self.handle_client, args=(connection, (peer_host, peer_port))).start()
        except ConnectionRefusedError:
            print(f"[ERROR] Connection refused: {ConnectionRefusedError}")

    def disconnect(self, connection, address):
        if connection == self.active_connection:
            self.active_connection = None
            self.connection_address = None
            print(f"[{self.host:}:{self.port}] Connection from {address} closed.")
        connection.close()

    def send_data(self, connection, address, data):
        if self.active_connection is None:
            print(f"[{self.host:}:{self.port}] Unable to send data, no active connection")
            return False
        try:
            print(f"[{self.host:}:{self.port}] Send data to {address}: {data}")
            connection.sendall(data.encode())
        except socket.error as e:
            print(f"[{self.host:}:{self.port}] Failed to send data. Error: {e}")
            self.disconnect(connection, address)

    def listen(self):
        self.socket.bind((self.host, self.port))
        self.socket.listen(1)
        print(f"[{self.host:}:{self.port}] Listening for connections on {self.host}:{self.port}")

        while True:
            connection, address = self.socket.accept()
            if self.active_connection is None:
                connection.sendall('free'.encode())
                threading.Thread(target=self.handle_client, args=(connection, address)).start()
            else:
                connection.sendall('busy'.encode())
                # connection.close()

    def handle_client(self, connection, address):
        while True:
            try:
                data = connection.recv(1024)
                if not data:
                    break

                print(f"[{self.host:}:{self.port}] Received data from {address}: {data.decode()}")

                if data.decode() == "bye" or data.decode() == "busy":
                    self.disconnect(connection, address)
                    return
                elif data.decode() == 'free':
                    print(f"[{self.host:}:{self.port}] Accepted connection from {address}")
                    self.active_connection = connection
                    self.connection_address = address
                    self.send_data(connection, address, 'pair?')
                elif data.decode() == 'pair?':
                    print(f"[{self.host:}:{self.port}] Accepted connection from {address}")
                    self.active_connection = connection
                    self.connection_address = address
                    print(f"[{self.host:}:{self.port}] Set connection with {address}? (Y/N)")
                    if input().lower() == "y":
                        self.send_data(connection, address, 'yes')
                    else:
                        self.send_data(connection, address, 'no')
                        self.disconnect(connection, address)

            except socket.error:
                break

        self.disconnect(connection, address)

    def stop(self):
        if self.active_connection is not None:
            self.disconnect(self.active_connection, self.connection_address)

        # Get the list of all threads in the process
        all_threads = threading.enumerate()

        # Terminate all threads
        for thread in all_threads:
            if thread.name != "MainThread":
                os._exit(0)

        self.socket.close()

    def start(self):
        listen_thread = threading.Thread(target=self.listen)
        listen_thread.start()


# python peer.py --address 127.0.0.1

# Example usage:
if __name__ == "__main__":
    # DEBUG
    parser = argparse.ArgumentParser()
    parser.add_argument("--address", help="Enter address for peer")
    args = parser.parse_args()

    PORT = 55000

    node = None

    if args.address is not None:
        node = Peer(args.address, PORT)
    else:
        node = Peer('127.0.0.1', PORT)
    node.start()

    address2 = None

    while True:
        msg = input('')
        if msg == 'connect':
            print('Enter address to connection: ')
            address2 = input()
            node.connect(address2, PORT)
        elif msg.split(' ')[0] == 'connect':
            try:
                address2 = msg.split(' ')[1]
                node.connect(address2, PORT)
            except:
                print('Invalid')
        elif msg == "exit":
            node.stop()
            break
        elif msg == 'faddr':
            print(node.addresses)
        elif msg == 'fc':
            if node.addresses:
                node.connect(node.addresses[0], PORT)
            else:
                print('Not found free addresses')
        elif msg == 'show':
            print(node.active_connection)
        elif msg.split(' ')[0] == 'm':
            node.send_data(node.active_connection, node.connection_address, msg.split(' ')[1])
            # pass
