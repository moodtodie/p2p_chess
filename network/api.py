import queue
import time

from peer import Peer
from service import get_local_ip


class ConnectionApi:
    def __init__(self, command_handler=None, ip_address=get_local_ip(), port=5500):
        self.peer = Peer(ip_address, port)
        self.__get_message__ = self.get_message

        if command_handler is not None:
            self.peer.start(command_handler)
            self.__get_message__ = command_handler
        else:
            self.peer.start(self.__put_message__)

        self.port = port
        self.is_connected = False
        self.command_queue = queue.Queue()

    def send_message(self, message):
        if self.is_connected:
            self.peer.send_data(self.peer.active_connection, self.peer.connection_address, message)
        else:
            print('Send message error: Connection was not established')

    def __put_message__(self, message):
        self.command_queue.put(message)

    def get_message(self):
        while self.command_queue.empty():
            time.sleep(0.3)
        msg = self.command_queue.get()
        return msg

    def connect(self, ip_address):
        pass

    def fast_connect(self):
        if self.is_connected:
            self.disconnect()

        self.peer.auto_connect = True

        while True:
            if self.peer.addresses and not self.is_connected:
                self.peer.connect(self.peer.addresses[0], self.port)
                time.sleep(0.2)

            self.update_status()

            if self.is_connected:
                break

    def disconnect(self):
        self.peer.auto_connect = False
        if self.is_connected:
            self.send_message('bye')
            self.is_connected = False
        else:
            print('Disconnect error: Connection was not established')

    def stop(self):
        if self.is_connected:
            self.disconnect()
        self.peer.stop()

    def update_status(self):
        if self.peer.active_connection:
            print('Successful status update')
            self.is_connected = True
