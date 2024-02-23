import argparse
import socket
import sys
import threading


class Peer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connections = []

    def find_connections(self):
        pass

    def connect(self, peer_host, peer_port):
        connection = socket.create_connection((peer_host, peer_port))

        self.connections.append(connection)
        print(f"[{self.host:}:{self.port}] Connected to {peer_host}:{peer_port}")

    def listen(self):
        self.socket.bind((self.host, self.port))
        self.socket.listen(10)
        print(f"[{self.host:}:{self.port}] Listening for connections on {self.host}:{self.port}")

        while True:
            connection, address = self.socket.accept()
            self.connections.append(connection)
            print(f"[{self.host:}:{self.port}] Accepted connection from {address}")
            threading.Thread(target=self.handle_client, args=(connection, address)).start()

    def send_data(self, data):
        for connection in self.connections:
            try:
                connection.sendall(data.encode())
            except socket.error as e:
                print(f"[{self.host:}:{self.port}] Failed to send data. Error: {e}")
                self.connections.remove(connection)

    def handle_client(self, connection, address):
        while True:
            try:
                data = connection.recv(1024)
                if not data:
                    break
                print(f"[{self.host:}:{self.port}] Received data from {address}: {data.decode()}")
            except socket.error:
                break

        print(f"[{self.host:}:{self.port}] Connection from {address} closed.")
        self.connections.remove(connection)
        connection.close()

    def start(self):
        listen_thread = threading.Thread(target=self.listen)
        listen_thread.start()


# python peer.py --port 8001 --init True --port_2 8000
# python peer.py --port 8000

# Example usage:
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", help="Enter port for peer: ", type=int)
    parser.add_argument("--init", help="It's the initiator: ", type=bool)
    parser.add_argument("--port_2", help="Enter port for peer 2: ", type=int)
    args = parser.parse_args()

    node = Peer("0.0.0.0", args.port)
    node.start()

    if args.init:
        node.connect('127.0.0.1', args.port_2)

    while True:
        msg = input('')
        if msg == "exit":
            # sys.exit(0)
            quit(1)
        node.send_data(msg)


    # node1 = Peer("0.0.0.0", 8000)
    # node1.start()
    #
    # node2 = Peer("0.0.0.0", 8001)
    # node2.start()
    #
    # # Give some time for nodes to start listening
    # import time
    #
    # time.sleep(2)
    #
    # node2.connect("127.0.0.1", 8000)
    # time.sleep(1)  # Allow connection to establish
    # node2.send_data("Hello from node2!")
