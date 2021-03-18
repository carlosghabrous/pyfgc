import logging
import struct

import pyfgc.channel_manager as channel_manager
import pyfgc.parsers.command as cmd
import pyfgc.fgc_response as rsp

# Logger
logger = logging.getLogger('pyfgc.protocols.serial_fgc')
logger.setLevel(logging.INFO)

# Constants
PROTOCOL_NAME = __name__.rsplit(".")[-1].split("_")[0]


class SerialFgc:
    def __init__(self):
        self.channel = None
        self.target_fgc = None
        self.target_gw = None
        self.timeout_s = None

    def connect(self, target_port, rbac_token, timeout_s):
        self.target_fgc = target_port.pop()
        self.target_gw = "SERIAL_" + self.target_fgc
        self.timeout_s = timeout_s

        try:
            self.channel = channel_manager.get_channel(self.target_fgc, PROTOCOL_NAME, self.target_gw)

        except Exception as e:
            raise RuntimeError(f"Could not open serial port {self.target_fgc}: {e}") from e

    def get(self, prop, get_option=None):
        return self._command_engine(prop, cmd.parse_get, cmd_argument=get_option)

    def set(self, prop, value):
        return self._command_engine(prop, cmd.parse_set, cmd_argument=value)

    def disconnect(self):
        try:
            channel_manager.free_channel(self.target_fgc, PROTOCOL_NAME, self.target_gw)

        except Exception:
            logger.exception(f"Failed to disconnect from gateway {self.target_gw}, device {self.target_fgc}")

        finally:
            self.channel = None

    def _command_engine(self, prop, command_encoder, cmd_argument):
        response_dict = dict()
        encoded_command = command_encoder(self.target_fgc, "serial", prop, cmd_argument)

        with self.channel.lock:
            try:
                self.channel.write(encoded_command)

            except Exception as e:
                raise RuntimeError(f"Exception while sending command {encoded_command.decode()} to port {self.target_fgc}: {e}") from e

            try:
                response_dict[self.target_fgc] = self._receive()

            except Exception as e:
                raise RuntimeError(f"Exception while receiving response to command {encoded_command.decode()} to port {self.target_fgc}: {e}") from e

        return rsp.FgcResponse(PROTOCOL_NAME, response_dict)

    def _receive(self):
        response = list()

        received = self.channel.read(1)
        while received not in [rsp.NET_RSP_VOID, rsp.NET_RSP_END, rsp.NET_RSP_BIN_FLAG, rsp.NET_ERROR]:
            response.append(received)
            received = self.channel.read(1)

        response.append(received)

        # Binary response
        if received == rsp.NET_RSP_BIN_FLAG:
            response_length_bytes = self.channel.read(4)
            response.append(response_length_bytes)

            # Format string !L -> ! (network = big endian), L (unsigned long)
            response_length_int = struct.unpack("!L", response_length_bytes)[0]

            byte_counter = 0
            while byte_counter < response_length_int:
                incoming_bytes = self.channel.read(response_length_int)
                byte_counter += len(incoming_bytes)
                response.append(incoming_bytes)

        byte_rsp = b"".join(response)
        return byte_rsp

