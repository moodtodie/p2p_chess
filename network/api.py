import queue
import random
import string
import time

from peer import Peer
from service import get_local_ip


class ConnectionApi:
    def __init__(self, command_handler=None, ip_address=get_local_ip(), port=5500):
        self.peer = Peer(ip_address, port)
        self.__get_message__ = self.get_message
        self.command_handler = self.__put_message__
        if command_handler is not None:
            self.command_handler = command_handler
        self.peer.start(self.command_handler)

        self.port = port
        self.is_connected = False
        self.command_queue = queue.Queue()

    def send_message(self, message):
        if self.is_connected:
            self.peer.send_data(self.peer.active_connection, self.peer.connection_address, message)
        else:
            print('Send message error: Connection was not established')

    def get_color(self) -> string:
        time.sleep(1.5)  # Synchronize
        while True:
            priority = random.randint(1, 1000)
            self.send_message(f'Pr: {priority}')
            enemy_priority = int(self.__get_message__().split()[1])

            if priority == enemy_priority:
                continue

            if priority < enemy_priority:
                return 'White'
            else:
                return 'Black'

    def __put_message__(self, message):
        self.command_queue.put_nowait(message)

    def get_message(self):
        try:
            while self.command_queue.empty():
                time.sleep(1)
                pass
            msg = self.command_queue.get()
            return msg
        except KeyboardInterrupt:
            return '^C'

    def connect(self, ip_address):
        pass

    def fast_connect(self):
        if self.is_connected:
            self.disconnect()

        self.peer.auto_connect = True

        while True:
            self.update_status()
            if self.peer.addresses and not self.is_connected:
                self.peer.connect(self.peer.addresses[0], self.port, self.command_handler)
                self.__get_message__()
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
            print(f'---=== Successful status update ===---')
            self.is_connected = True
        else:
            self.is_connected = False
