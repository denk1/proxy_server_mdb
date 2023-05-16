#!/usr/bin/python3.10
import asyncio
import struct
import time
import numpy as np


class EchoClientProtocol(asyncio.Protocol):
    def __init__(self, message, on_con_lost):
        self.message = message
        self.on_con_lost = on_con_lost
        self.count = 0
        self.initial_connection = bytearray()
        self.initial_connection.append(0x79)
        self.initial_connection.append(0x92)
        

    def connection_made(self, transport):
        self.transport = transport
        transport.write(self.initial_connection)
        print('connection made')
        

    def data_received(self, data):
        print('test!')
        l = np.arange(0.0, 100.0, 1.0)
        idx = np.arange(len(l))
        l = np.insert(l, idx[:], 0)
        if 0x79 == data[0] and 0x93 == data[1]:
            connection_admittion = bytearray()
            connection_admittion.append(0x79)
            connection_admittion.append(0x94)
            self.transport.write(connection_admittion)
        elif 0x44 == data[0] and 0x47 == data[1]:
            complited_task_flag = bytearray()
            complited_task_flag.append(0x44)
            complited_task_flag.append(0x48)
            print(data)
            print(complited_task_flag)
            packed_n = struct.pack('i', len(l));
            packed_f = struct.pack('200f',  *l[:])
            total_quantity = len(complited_task_flag) + len(packed_n) + len(packed_f)
            self.transport.write(complited_task_flag + packed_n + packed_f)
        
            

    def connection_lost(self, exc):
        print('The server closed the connection')
        
        


async def main():
    # Get a reference to the event loop as we plan to use
    # low-level APIs.
    loop = asyncio.get_running_loop()

    on_con_lost = loop.create_future()
    message = 'Hello World!'

    transport, protocol = await loop.create_connection(
        lambda: EchoClientProtocol(message, on_con_lost),
        'localhost', 15556)

    # Wait until the protocol signals that the connection
    # is lost and close the transport.
    try:
        await on_con_lost
    finally:
        transport.close()


asyncio.run(main())
