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
        self.free_connection = None
        self.connection_address = None
        # Flags
        self.is_real_connection = False
        self.address_is_vacant = False
        self.address_is_busy = False
        self.connection_was_lost = False
        # self.is_reconnect = False

        threading.Thread(target=self.find_connections, args=()).start()

    def find_connections(self):
        while True:
            if self.active_connection is None:
                # subnet = '192.168.0' # LAN
                subnet = '127.0.0'  # Debug
                addresses = find_devices_with_port_open(subnet, self.port)
                try:
                    addresses.remove(self.host)
                except ValueError:
                    pass
                print(f'[find_connections] Any  {addresses}')
                if self.active_connection is None:
                    self.find_free_connections(addresses)
                print(f'[find_connections] Free {self.addresses}')

    def find_free_connections(self, addresses):
        free_addresses = []
        if self.active_connection is None:
            for address in addresses:
                if self.active_connection is None:
                    self.service_connection(address, self.port)
                start_time = time.time()
                while True:
                    if self.address_is_vacant is True:
                        free_addresses.append(address)
                        if self.active_connection is not self.free_connection:
                            self.disconnect(self.free_connection, address)
                        break
                    elif self.address_is_busy:
                        break
                    elif time.time() - start_time > 3:
                        break

            self.address_is_vacant = False
            self.address_is_busy = False

        self.addresses.clear()
        self.addresses = free_addresses

    def reconnecting_socket(self, port, timeout=5, retries=5):
        self.connection_was_lost = True
        for attempt in range(retries):
            try:
                sock = socket.create_connection((self, port), timeout)
                self.connection_was_lost = False
                return sock
            except socket.error as e:
                print(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise

    def connect(self, peer_host, peer_port):
        self.is_real_connection = True
        self.service_connection(peer_host, peer_port)

    def service_connection(self, peer_host, peer_port):
        try:
            # if self.is_real_connection:
            #     connection = self.reconnecting_socket(peer_host, peer_port)
            # else:
            connection = socket.create_connection((peer_host, peer_port))

            if self.is_real_connection:
                if self.active_connection is not None:
                    self.disconnect(self.active_connection, self.connection_address)

                self.active_connection = connection
                self.connection_address = f'({peer_host}:{peer_port})'
                print(f"[{self.host:}:{self.port}] Connected to {peer_host}:{peer_port}")

            time.sleep(1)
            threading.Thread(target=self.handle_client, args=(connection, (peer_host, peer_port))).start()
        except ConnectionRefusedError:
            print(f"[ERROR] Connection refused: {ConnectionRefusedError}")

    # def disconnect(self, connection, address):
    #     pass

    def disconnect(self, connection, address):
        # print(f'[disconnect] Step 1.0 | is real - {self.is_real_connection}')
        if not self.is_real_connection:
            print(f'[disconnect] Step 2.1 | free connect - {self.free_connection}')
            self.free_connection = None

        print(f'[disconnect] Step 1.1 | is real - {self.is_real_connection} | is vacant {self.address_is_vacant}')
        self.is_real_connection = False
        self.address_is_vacant = False

        if connection == self.active_connection:
            print(f'[disconnect] Step 1.0 | active connect - {self.active_connection}')
            self.active_connection = None
            self.connection_address = None

        print(f"[{self.host:}:{self.port}] Connection from {address} closed.")
        try:
            connection.close()
        except Exception as e:
            print(f'Close connection ERROR: {e}')

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
            try:
                connection, address = self.socket.accept()
                if self.active_connection is None:
                    connection.sendall('free'.encode())
                    threading.Thread(target=self.handle_client, args=(connection, address)).start()
                else:
                    connection.sendall('busy'.encode())
            except ConnectionResetError:
                print(f"[{self.host:}:{self.port}] ConnectionResetError: {ConnectionResetError.mro()}")
                pass

    def handle_client(self, connection, address):
        while True:
            try:
                data = connection.recv(1024)
                if not data:
                    break

                print(f"[{self.host:}:{self.port}] Received data from {address}: {data.decode()}")

                if data.decode() == "busy":
                    self.address_is_busy = True
                    self.disconnect(connection, address)
                    return
                elif data.decode() == "bye":
                    self.disconnect(connection, address)
                    return
                elif data.decode() == 'free':
                    if self.is_real_connection:
                        print(f"[{self.host:}:{self.port}] Accepted connection from {address}")
                        self.active_connection = connection
                        self.connection_address = address
                        self.send_data(connection, address, 'pair?')
                    else:
                        self.free_connection = connection
                    self.address_is_vacant = True
                elif data.decode() == 'pair?':
                    print(f"[{self.host:}:{self.port}] Accepted connection from {address}")
                    self.is_real_connection = True
                    self.active_connection = connection
                    self.connection_address = address

                    # Replace here
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

    if args.address is None:
        node = Peer('127.0.0.1', PORT)
    else:
        node = Peer(args.address, PORT)
    node.start()

    address2 = None

    while True:
        msg = input('')
        if msg.split(' ')[0] == 'connect':
            try:
                address2 = msg.split(' ')[1]
                node.connect(address2, PORT)
            except:
                print('Invalid')
        elif msg == "exit":
            node.stop()
            break
        elif msg == 'bye':
            node.disconnect(node.active_connection, node.connection_address)
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
            node.send_data(node.active_connection, node.connection_address, " ".join(msg.split(' ')[1:]))
