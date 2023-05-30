#!/usr/bin/python3.10


import asyncio
from operator import index
import os
from enum import Enum
from datetime import datetime


def get_time():
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S.%f")
    
    return "[" + current_time + "]"

class Direction(Enum):
    CAR = 1 # detection.py
    BMD = 2 # BPR_NAMI
    MONITOR = 3 # Situation monitor PATH
    MONITOR_SITUATION = 4 # Situation monitor OBSTACLES
    


direction_names_dict = {Direction.CAR: "Car", Direction.BMD: "BPR_NAMI", Direction.MONITOR: "MONITOR PATH", Direction.MONITOR_SITUATION: "MONITOR OBSTACLES"}
# class MarkedTransport(asyncio.selector_events._SelectorSocketTransport):
#    def __init__(self, parent):
#        super().__init__(parent)

directionPairs = {Direction.CAR: [Direction.BMD, Direction.MONITOR_SITUATION], Direction.BMD: [Direction.CAR, Direction.MONITOR]}

headers_dict = {
    (0x79, 0x90): ((0x79, 0x91), (0x79, 0x11),  Direction.MONITOR_SITUATION, ((0x44, 0x48), (0x44, 0x47))),
    (0x79, 0x92): ((0x79, 0x93), (0x79, 0x94),  Direction.BMD, ((0x44, 0x48), (0x44, 0x47))),
    (0x79, 0x95): ((0x79, 0x96), (0x79, 0x97), Direction.CAR, ((0x44, 0x47), (0x44, 0x48))),
    (0x79, 0x98): ((0x79, 0x99), (0x79, 0x12), Direction.MONITOR, ((0x44, 0x47), (0x44, 0x48))),
}


class MsgSender:
    def __init__(self, loop) -> None:
        self.loop = loop
        
        
    
    def msg_sending(self, loop, transport, msg):
        transport.write(msg)
        #loop.stop()
        
    def send_data(self, transport, data):
        try:
            self.loop.call_soon(self.msg_sending, self.loop, transport, data)
        except Exception as e:
            print(str(e))
        #try:
        #    self.loop.run_forever()
        #finally:
        #    loop.close()
        
    

class ConnectionDefenition:
    clients = dict()
    def __init__(self, index):
        self.connected = False
        self.first_sending = True

        self.index = index

    def admitted(self):
        self.connected = True

    def is_connected(self):
        return self.connected

    def is_first_sending(self):
        return self.first_sending

    def first_check_header(self, data):
        try:
            self.rest_headers = headers_dict[(data[0], data[1])]
        
            return True
        except KeyError:
            print('unknown packet')
            return False

    def send_admition(self):
        data_in_tuple = self.rest_headers[0]
        return bytes(data_in_tuple)

    def make_connected(self, data):
        self.client_type = self.rest_headers[2]
        b0 = data[0]
        b1 = data[1]
        #return data[0] == self.rest_headers[1][0] and data[1] == self.rest_headers[1][1]
        return b0 == self.rest_headers[1][0] and b1 == self.rest_headers[1][1]

    def is_request(self, data):
        return data[0] == self.rest_headers[3][0][0] and data[1] == self.rest_headers[3][0][1]

    def __eq__(self, another) -> bool:
        return self.index == another.index



class EchoServerProtocol(asyncio.Protocol):
    __index = 0

    def __init__(self):
        try:
            self.connection_defenition = ConnectionDefenition(self.__class__.__index)
            self.__class__.__index += 1
        except:
            print("error")

    def init(self):
        self.is_make_decision_server = False
        self.is_a_car = False
        self.is_the_first_data = True

    def client_cheaker(self):
        if self.is_make_decision_server:
            print('This is the maker decision block')
        elif self.is_a_car:
            print('This is a car')
        else:
            print('This has been gotten from an unknown client!')

    def connection_made(self, transport):
        self.init()
        self.peername = transport.get_extra_info('peername')
        self.transport = transport
        print('Connection from {0} N {1}'.format(self.peername, self.__index))

    def data_received(self, data):
        message = data

        if self.connection_defenition.is_first_sending():
            if self.connection_defenition.first_check_header(data):
                try:

                    self.transport.write(
                        self.connection_defenition.send_admition())
                    self.connection_defenition.first_sending = False
                    print('Send: {!r}'.format(message))
                except Exception:
                    print('The message has not been sent')
        elif not self.connection_defenition.is_connected():
            try:
                if self.connection_defenition.make_connected(message):
                    self.connection_defenition.connected = True
                    ConnectionDefenition.clients[self.connection_defenition.client_type] = self.transport
                    print('the connection to {0} has just been established '.format(direction_names_dict[self.connection_defenition.client_type]))
            except Exception as e:
                print(f'The result message has not been resent {0}'.format(str(e)))
        elif self.connection_defenition.is_request(message):
            for clnt in directionPairs[self.connection_defenition.client_type]:
                if clnt in ConnectionDefenition.clients.keys():
                    client_tns = ConnectionDefenition.clients[clnt]
                    msg_sender.send_data(client_tns, message)
                    print(get_time(), direction_names_dict[self.connection_defenition.client_type],  "->", len(message), "->", direction_names_dict[clnt]  )
                    #client_tns.write(message)
        else:
            print('The recieved message has not been recognized:(')
            print(data[0], data[1])

       
    def connection_lost(self, exc):
        # The socket has been closed        
        ConnectionDefenition.clients.pop(self.connection_defenition.client_type)
        print('The connection with {0} has been lost!'.format(direction_names_dict[self.connection_defenition.client_type]))
        print(len(ConnectionDefenition.clients))

    def __eq__(self, another) -> bool:
        return self.index == another.index


# Get a reference to the event loop as we plan to use

# low-level APIs.

loop = asyncio.new_event_loop()
msg_sender = MsgSender(loop)
connections = []

coro = loop.create_server(
    lambda: EchoServerProtocol(),
    os.environ.get('MY_SERVICE_ADDRESS', 'localhost'),
    os.environ.get('MY_SERVICE_PORT', 15556))

server = loop.run_until_complete(coro)

try:
    loop.run_forever()
except KeyboardInterrupt:
    pass

server.close()
loop.run_until_complete(server.wait_closed())
loop.close()
