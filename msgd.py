#!/usr/bin/env python3

import argparse
import asyncio
import traceback
from asyncio.streams import StreamReader, StreamWriter
from collections import namedtuple, defaultdict
from typing import List, Dict

from commands import CommandRunner

Message = namedtuple('Message', ['subject', 'message'])


# NOTE TO THE TA's: I asked the Professor and he said it was fine to use asyncio rather than epoll directly.

def start(port=8080):
    messages = defaultdict(list)
    keys = {}

    async def handle_client(reader: StreamReader, writer: StreamWriter):
        session = MessagingSession(messages, keys, reader, writer)
        await session.handle_client()

    return asyncio.start_server(handle_client, 'localhost', port)


class MessagingSession(CommandRunner):
    def __init__(self, messages: Dict[bytes, List[Message]], keys: Dict[bytes, bytes],
                 reader: StreamReader, writer: StreamWriter):
        self.messages = messages
        self.keys = keys
        self.reader = reader
        self.writer = writer

    async def handle_client(self):
        try:
            while True:
                try:
                    line = (await self.reader.readline()).decode()
                    print(line)
                    result = await self.run_command(line)
                    if result is None:
                        result = b'OK\n'
                    self.writer.write(result)
                except Exception as e:
                    print(traceback.format_exc())
                    self.writer.write(b'error ' + str(e).encode() + b'\n')
                await self.writer.drain()
        except ConnectionError:
            pass

    async def cmd_put(self, name: bytes, subject: bytes, length: int):
        assert isinstance(length, int)
        message = await self.reader.readexactly(length)
        self.messages[name].append(Message(subject, message))

    async def cmd_list(self, name: bytes):
        messages = self.messages.get(name, [])
        data = b'list %d\n' % len(messages)
        data += b''.join(b'%d %s\n' % (index + 1, message.subject)
                         for index, message in enumerate(messages))
        return data

    async def cmd_get(self, name: bytes, index: int):
        message = self.messages[name][index - 1]
        return b'message %s %d\n%s' % (message.subject, len(message.message), message.message)

    async def cmd_store_key(self, name: bytes, length: int):
        key = await self.reader.readexactly(length)
        self.keys[name] = key

    async def cmd_get_key(self, name: bytes):
        key = self.keys[name]
        return b'key %d\n%s' % (len(key), key)

    async def cmd_reset(self):
        self.messages.clear()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', metavar='port', default=8081, dest='port', type=int,
                        help='port number of the messaging server')
    parser.add_argument('-d', action='store_true', dest='debug', help='print debugging information')
    args = parser.parse_args()
    loop = asyncio.get_event_loop()
    server = loop.run_until_complete(start(args.port))
    print('Serving on {}'.format(server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    print('Stopping...')
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()


if __name__ == '__main__':
    main()
