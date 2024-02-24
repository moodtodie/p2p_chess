import argparse
import os
import socket
import sys
import threading
import time


class Peer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connections = []
        self.addresses = []

    def find_connections(self):
        pass

    def connect(self, peer_host, peer_port):
        connection = socket.create_connection((peer_host, peer_port))

        self.connections.append(connection)
        print(f"[{self.host:}:{self.port}] Connected to {peer_host}:{peer_port}")
        time.sleep(1)
        threading.Thread(target=self.handle_client, args=(connection, (peer_host, peer_port))).start()

    def disconnect(self, connection, address):
        print(f"[{self.host:}:{self.port}] Connection from {address} closed.")
        self.connections.remove(connection)
        connection.close()

    def disconnect_all(self):
        for connection in self.connections:
            self.connections.remove(connection)
            connection.close()
        print(f"[{self.host:}:{self.port}] All connection closed.")

    def send_data(self, data):
        for connection in self.connections:
            try:
                print(f"[{self.host:}:{self.port}] Send data: {data}")
                connection.sendall(data.encode())
            except socket.error as e:
                print(f"[{self.host:}:{self.port}] Failed to send data. Error: {e}")
                self.connections.remove(connection)

    def listen(self):
        self.socket.bind((self.host, self.port))
        self.socket.listen(10)
        print(f"[{self.host:}:{self.port}] Listening for connections on {self.host}:{self.port}")

        while True:
            connection, address = self.socket.accept()
            self.connections.append(connection)
            print(f"[{self.host:}:{self.port}] Accepted connection from {address}")
            threading.Thread(target=self.handle_client, args=(connection, address)).start()

    def handle_client(self, connection, address):
        while True:
            try:
                data = connection.recv(1024)
                if not data:
                    break
                print(f"[{self.host:}:{self.port}] Received data from {address}: {data.decode()}")
                if data.decode() == "bye":
                    self.disconnect(connection, address)
                    return
            except socket.error:
                break

        self.disconnect(connection, address)

    def stop(self):
        self.disconnect_all()

        # Get the list of all threads in the process
        all_threads = threading.enumerate()

        # Terminate all threads
        for thread in all_threads:
            if thread.name != "MainThread":
                # print(f"Terminating thread {thread.name} (ID={thread.ident})")
                os._exit(0)

        self.socket.close()

    def start(self):
        listen_thread = threading.Thread(target=self.listen)
        listen_thread.start()


# python peer.py --address 127.0.0.1

# Example usage:
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--address", help="Enter address for peer: ")
    args = parser.parse_args()

    PORT = 55000

    node = Peer(args.address, PORT)
    node.start()

    address2 = None

    while True:
        msg = input('')
        if msg == 'connect':
            print('Enter address to connection: ')
            address2 = input()
            node.connect(address2, PORT)
        elif msg == "exit":
            node.stop()
            sys.exit(0)
        elif msg == 'show':
            print(node.connections)
        else:
            node.send_data(msg)
