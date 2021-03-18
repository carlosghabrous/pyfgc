import struct
import logging
import asyncio
import concurrent.futures

from typing import Callable

from .. import channel_manager
import pyfgc.parsers.command as cmd
import pyfgc.fgc_response as rsp

# Logger
logger = logging.getLogger('pyfgc.protocols.sync_fgc')
logger.setLevel(logging.INFO)

# Constants
PROTOCOL_NAME = __name__.rsplit(".")[-1].split("_")[0]
HANDSHAKE_CHAR = '+'
PORT = 1905

class AsyncFgcProtocol(asyncio.Protocol):
    """
    Asynchronous TCP interaction with a Gateway/FGC
    """

    def __init__(self, loop: asyncio.AbstractEventLoop):
        """
        This constructor is called only by the Loop.create_connection method

        :param loop:
        """
        self.loop = loop
        self.transport = None
        self.handshake_made = False
        self.gateway = None
        self.raw_mode = False
        self.raw_stream = asyncio.StreamReader()
        self.buffer = bytearray()
        self.buffer_wait_n = 0
        self.commands = dict()
        self.tag_counter = 0
        self.connection_lost_callbacks = set()

    def connection_made(self, transport: asyncio.Transport):
        """
        When connection has been made

        :param transport:
        :return:
        """
        self.transport = transport
        self.gateway = transport.get_extra_info("peername")
        self.__send_handshake()

    def add_connection_lost_callback(self, callback: Callable):
        """
        Run (non-coroutine) callback when connection is lost
        """
        self.connection_lost_callbacks.add(callback)

    def connection_lost(self, exc):
        """
        When connection has been lost

        :param exc:
        :return:
        """
        # TODO: Log exception
        for fut in self.commands.values():
            fut.cancel()
        if exc:
            for cb in self.connection_lost_callbacks:
                cb()

    def data_received(self, payload: bytes):
        """
        When something is received from the socket

        :param payload:
        :return:
        """
        self.buffer += payload

        if not self.handshake_made:
            # handshake
            self.__process_handshake()
        elif self.raw_mode:
            # Provide data to stream
            self.__process_raw_stream()
        else:
            # Parse result into a response
            self.__process_responses(payload)

    def eof_received(self):
        """
        When the other end will not send more data

        :return:
        """
        super().eof_received()

    async def enable_rterm_mode(self, channel, command=None):
        """
        Use raw communication instead of NCRP protocol.
        """
        command = "CLIENT.RTERMLOCK" if command is None else command
        result = await self.set(command, str(channel))
        result.value

        self.raw_mode = True
        self.data_received(b"") # Flush data to StreamReader

    def __send_handshake(self) -> None:
        """
        Send handshake to the gateway
        """
        self.transport.write(b'+')

    def __process_handshake(self) -> None:
        """
        Handle character when in 'waiting for handshake' mode

        :param payload:
        :return:
        """
        # Remove first character from buffer
        ack_char = chr(self.buffer.pop(0))
        if ack_char != HANDSHAKE_CHAR:
            raise ConnectionError(f"Handshake with gateway {self.gateway} not successful (received {ack_char} vs {HANDSHAKE_CHAR})!")
        self.handshake_made = True

    def __process_raw_stream(self):
        # Just parse entire buffer into StreamReader
        self.raw_stream.feed_data(self.buffer)
        self.buffer.clear()

    def __extract_response(self):
        """
        Gets a response from the buffer
        :return: (tag, raw response, wait for N characters)
        """
        # NOTE: 'memoryview' will make the analysis of the buffer much more efficient.
        # For example, for slicing bytearray without copying its contents.

        # Check type of response (binary/non-binary/error)
        match = rsp.NCRP_BEGIN.search(self.buffer)

        if match and match.group(3) is not None:
            # The next response is binary
            span_begin, span_end = match.span()
            tag = match.group(1).decode()
            length = struct.unpack('>I', match.group(3))[0]

            rsp_end = span_end + length
            last_char = rsp_end + 2
            if len(self.buffer) < last_char:
                # BIN response is not ready. Wait for another N characters.
                wait_n = last_char - len(self.buffer)
                return (tag, None, wait_n) # Wait for another N characters

            # Return response and character \xff at postion #0
            with memoryview(self.buffer) as buffer_view:
                raw_response = bytes(buffer_view[span_begin: last_char])
                response = rsp.FgcSingleResponse(PROTOCOL_NAME, raw_response)
            del self.buffer[:last_char]

            return (tag, response, None) # Response is valid

        elif match and match.group(2) is not None:
            # The next response is non-binary
            span_begin, span_end = match.span()
            tag = match.group(1).decode()

            rsp_end = self.buffer.find(b"\n;", span_end)
            if rsp_end < 0:
                return (tag, None, None) # Wait for another ? characters

            last_char = rsp_end + 2

            with memoryview(self.buffer) as buffer_view:
                raw_response = bytes(buffer_view[span_begin: last_char])
                response = rsp.FgcSingleResponse(PROTOCOL_NAME, raw_response)
            del self.buffer[:last_char]

            return (tag, response, None) # Response is valid

        elif match and match.group(4) is not None:
            # The next response is an error
            span_begin, span_end = match.span()
            tag = match.group(1).decode()

            with memoryview(self.buffer) as buffer_view:
                raw_response = bytes(buffer_view[span_begin: span_end])
                response = rsp.FgcSingleResponse(PROTOCOL_NAME, raw_response)
            del self.buffer[:span_end]

            return (tag, response, None)

        # If no match found
        return (None, None, None) # Wait for another ? characters

    def __process_responses(self, payload: bytes):

        self.buffer_wait_n = max(self.buffer_wait_n - len(payload), 0)

        # Check for '\n' only on new data (payload).
        if payload != rsp.NET_RSP_VOID and \
            (self.buffer_wait_n > 0 or rsp.NET_RSP_END not in payload):
            return

        while True:
            result = self.__extract_response()
            tag, raw_response, wait_n = result
            if tag and raw_response:
                self.__resolve_pending_request(tag, raw_response)
            elif wait_n:
                self.buffer_wait_n = wait_n
                break
            else:
                break

    def __new_tag(self):
        self.tag_counter += 1
        return "{:08X}".format(self.tag_counter)[:8]

    def __register_pending_request(self, tag: str) -> asyncio.Future:
        """
        Register a pending command. The future will be resolved by the 'data_received' callback

        :param tag:
        :return:
        """
        self.commands[tag] = self.loop.create_future()
        return self.commands[tag]

    def __resolve_pending_request(self, tag: str, result: dict) -> None:
        """
        Resolves a previously pending request
        :param result:
        :return:
        """
        try:
            future = self.commands[tag]
        except KeyError as err:
            raise KeyError(f"Tag {tag} is unknown.") from err
        else:
            del self.commands[tag]

        try:
            future.set_result(result)
        except asyncio.InvalidStateError as err:
            # During termination, futures may be cancelled by their callers
            if not future.cancelled():
                raise RuntimeError("Future was already set before.") from err

    def disconnect(self):
        """
        Disconnects from the FGC
        """
        self.transport.close()

    async def set(self, prop: str, value, device: str = ''):
        """
        Asynchronous set. Will resolve when the response arrives.

        :param prop: property to set
        :param value: value
        :param device: device that should handle the command
        :return: future that will be resolved when the response arrived
        """
        tag = self.__new_tag()
        command = cmd.parse_set(device, "async", prop, value, tag=tag)
        future = self.__register_pending_request(tag)
        await self.send(command)
        return await future

    async def get(self, prop: str, get_option=None, device: str = ''):
        """
        Asynchronous get. Will resolve when the response arrives.

        :param prop: property to get
        :param device: device that should handle the command
        :return: future that will be resolved when the response arrived
        """
        tag = self.__new_tag()
        command = cmd.parse_get(device, "async", prop, get_option, tag=tag)
        future = self.__register_pending_request(tag)
        await self.send(command)
        return await future

    def get_stream_reader(self):
        """
        Returns a StreamReader object buffering the received raw data.
        :return: asyncio.StreamReader
        """
        return self.raw_stream

    async def send(self, payload: bytes):
        """
        Send given payload to the gateway

        :param payload: Bytes to send
        """
        if self.transport and not self.transport.is_closing():
            self.transport.write(payload)
        else:
            raise RuntimeError("Protocol is not open.")


class AsyncFgc:

    protocol_dict = dict()
    protocol_users = dict()
    loop_locks = dict()

    def __init__(self):
        self.protocol   = None
        self.loop       = None
        self.target_fgc = None
        self.target_gw  = None
        self.rbac_token = None
        self.timeout_s  = None
        self.async_lock = None

    async def connect(self, loop, target_tuple, rbac_token, timeout_s):

        self.target_fgc, self.target_gw = target_tuple.pop()
        self.rbac_token = rbac_token
        self.timeout_s  = timeout_s
        self.loop = loop

        try:
            self.async_lock = self.loop_locks[self.loop]
        except KeyError:
            self.async_lock = asyncio.Lock()
            self.loop_locks[self.loop] = self.async_lock

        async with self.async_lock:
            try:
                self.protocol = self.protocol_dict[self.loop, self.target_gw]
                self.protocol_users[self.protocol] += 1
            except KeyError:
                _, self.protocol = await asyncio.wait_for(self.loop.create_connection(lambda: AsyncFgcProtocol(self.loop), self.target_gw, PORT), timeout=self.timeout_s)
                self.protocol_dict[self.loop, self.target_gw] = self.protocol
                self.protocol_users[self.protocol] = 1

                try:
                    await self._set_token()
                except asyncio.TimeoutError as err:
                    del self.protocol_dict[self.loop, self.target_gw]
                    del self.protocol_users[self.protocol]
                    if self.protocol:
                        self.protocol.disconnect()
                    self.protocol = None
                    raise asyncio.TimeoutError(f"S {self.target_gw}:CLIENT.TOKEN timeout.")

            # If for some future reason the protocol fails, it should be disconnected properly
            self.protocol.add_connection_lost_callback(
                lambda: asyncio.run_coroutine_threadsafe(self.disconnect(), loop)
            )

    async def get(self, prop, get_option=None):
        if not self.protocol:
            raise RuntimeError("No protocol.")
        try:
            return await asyncio.wait_for(self.protocol.get(prop, get_option=get_option, device=self.target_fgc), timeout=self.timeout_s)
        except asyncio.TimeoutError as err:
            raise asyncio.TimeoutError(f"G {self.target_fgc}:{prop} timeout.")

    async def set(self, prop, value):
        if not self.protocol:
            raise RuntimeError("No protocol.")
        try:
            return await asyncio.wait_for(self.protocol.set(prop, value, device=self.target_fgc), timeout=self.timeout_s)
        except asyncio.TimeoutError as err:
            raise asyncio.TimeoutError(f"S {self.target_fgc}:{prop} timeout.")

    async def disconnect(self):
        async with self.async_lock:
            if not self.protocol:
                return
            self.protocol_users[self.protocol] -= 1
            if self.protocol_users[self.protocol] <= 0:
                del self.protocol_dict[self.loop, self.target_gw]
                del self.protocol_users[self.protocol]
                self.protocol.disconnect()
                self.protocol = None

    async def _set_token(self):

        if self.rbac_token is None:
            logger.warning(f"Received None token for gateway {self.target_gw}. Token not set.")
            return

        try:
            set_result = await asyncio.wait_for(self.protocol.set("CLIENT.TOKEN", self.rbac_token), timeout=self.timeout_s)
            set_result.value
        except asyncio.TimeoutError as err:
            raise asyncio.TimeoutError(f"S {self.target_gw}:CLIENT.TOKEN timeout.")




# EOF
