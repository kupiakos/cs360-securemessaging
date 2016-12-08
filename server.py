import asyncio
from asyncio.streams import StreamReader, StreamWriter

from commands import CommandRunner


async def start(port=8080):
    await asyncio.start_server(handle_client, 'localhost', port)


async def handle_client(reader: StreamReader, writer: StreamWriter):
    session = MessagingSession(reader, writer)
    session.handle_client()


class MessagingSession(CommandRunner):
    def __init__(self, reader: StreamReader, writer: StreamWriter):
        self.reader = reader
        self.writer = writer

    async def handle_client(self):
        line = await self.reader.readline()

