import socket
import threading
import time

from service import find_devices_with_port_open, get_subnet


class Peer:
    def __init__(self, host, port: int, auto_connect=False):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))
        self.socket.listen(1)
        print(f"[{self.host:}:{self.port}] Listening for connections on {self.host}:{self.port}")

        self.addresses = []
        self.active_connection = None
        self.free_connection = None
        self.connection_address = None
        # Flags
        self.auto_connect = auto_connect
        self.is_real_connection = False
        self.address_is_vacant = False
        self.address_is_busy = False
        self.stop_loops = False

        threading.Thread(target=self.find_connections, args=()).start()

    def find_connections(self):
        while not self.stop_loops:
            if self.active_connection is None:
                # print(f'[debug] [{round(time.time(), 3)}] socket: {self.socket}')
                subnet = get_subnet(self.host)
                addresses = find_devices_with_port_open(subnet, self.port)
                try:
                    addresses.remove(self.host)
                except ValueError:
                    pass
                # print(f'[debug] [{round(time.time(), 3)}] addresses: {addresses}')
                if self.active_connection is None:
                    self.find_free_connections(addresses)
                else:
                    break
                if self.active_connection is None:
                    print(f'[find_connections] Free {self.addresses}')
            else:
                time.sleep(1)

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
                            self.disconnect(self.free_connection)
                        break
                    elif self.address_is_busy:
                        break
                    elif time.time() - start_time > 3:
                        break

            self.address_is_vacant = False
            self.address_is_busy = False

        self.addresses.clear()
        self.addresses = free_addresses

    def connect(self, peer_host, peer_port, handler):
        self.is_real_connection = True
        self.service_connection(peer_host, peer_port, handler)

    def service_connection(self, peer_host, peer_port, handler=None):
        try:
            connection = socket.create_connection((peer_host, peer_port))

            # if self.is_real_connection:
            if handler is not None:
                if self.active_connection is not None:
                    self.disconnect(self.active_connection)

                self.active_connection = connection
                self.connection_address = f'({peer_host}:{peer_port})'
                print(f"[{self.host:}:{self.port}] Connected to {peer_host}:{peer_port}")

            time.sleep(1)
            threading.Thread(target=self.handle_client, args=(connection, (peer_host, peer_port), handler)).start()
        except ConnectionRefusedError:
            print(f"[ERROR] Connection refused: {ConnectionRefusedError}")

    def disconnect(self, connection):
        if not self.is_real_connection:
            self.free_connection = None

        self.is_real_connection = False
        self.address_is_vacant = False

        if connection == self.active_connection:
            self.active_connection = None
            self.connection_address = None

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
            self.disconnect(connection)

    def listen(self, handler):
        while not self.stop_loops:
            try:
                connection, address = self.socket.accept()
                if self.active_connection is None:
                    connection.sendall('free'.encode())
                    threading.Thread(target=self.handle_client, args=(connection, address, handler)).start()
                else:
                    connection.sendall('busy'.encode())
            except socket.error as e:
                if not self.stop_loops:
                    print(f"[{self.host:}:{self.port}] (listen) {e}")

    def handle_client(self, connection, address, handler=None):
        while not self.stop_loops:
            try:
                data = connection.recv(1024)
                if not data:
                    break

                print(f"[{self.host:}:{self.port}] Received data from {address}: {data.decode()}")

                if data.decode() == "busy":
                    self.address_is_busy = True
                    self.disconnect(connection)
                    return
                elif data.decode() == "bye":
                    self.disconnect(connection)
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

                    if self.active_connection is not None:
                        self.send_data(connection, address, 'no')
                        self.disconnect(connection)
                    elif self.auto_connect:
                        self.send_confirm_signal(connection, address)
                    else:
                        # self.pairing_request(connection, address)
                        self.send_data(connection, address, 'no')
                        self.disconnect(connection)
                elif handler is not None:
                    handler(data.decode())
            except socket.error:
                break

        if self.active_connection is not None:
            self.disconnect(connection)

    def send_confirm_signal(self, connection, address):
        self.is_real_connection = True
        self.active_connection = connection
        self.connection_address = address
        self.send_data(connection, address, 'yes')

    def pairing_request(self, connection, address):
        print(f"[{self.host:}:{self.port}] Set connection with {address}? (Y/N)")
        if input().lower() == "y":
            self.send_confirm_signal(connection, address)
        else:
            self.send_data(connection, address, 'no')
            self.disconnect(connection)

    def stop(self):
        if self.active_connection is not None:
            self.disconnect(self.active_connection)

        self.stop_loops = True
        self.socket.close()

    def start(self, handler):
        threading.Thread(target=self.listen, args=(handler,)).start()
