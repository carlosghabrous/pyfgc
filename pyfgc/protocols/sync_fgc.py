import logging
import struct
import traceback

from .. import channel_manager
import pyfgc.parsers.command as cmd
import pyfgc.fgc_response as rsp

# Logger
logger = logging.getLogger('pyfgc.protocols.sync_fgc')
logger.setLevel(logging.INFO)

# Constants
PROTOCOL_NAME = __name__.rsplit(".")[-1].split("_")[0]

class SyncFgc:
    def __init__(self):
        self.channel    = None
        self.target_fgc = None
        self.target_gw  = None
        self.rbac_token = None
        self.timeout_s  = None

    def connect(self, target_tuple, rbac_token, timeout_s):
        self.target_fgc, self.target_gw = target_tuple.pop()
        self.rbac_token = rbac_token
        self.timeout_s  = timeout_s

        try:
            self.channel = channel_manager.get_channel(self.target_fgc, PROTOCOL_NAME, self.target_gw)

        except Exception as e:
            raise RuntimeError(f"Could not open socket with gateway {self.target_gw} for fgc {self.target_fgc}: {e}") from e

        #TODO: try moving set token to channel_manager
        with self.channel.lock:
            try:
                self._set_token()

            except Exception as e:
                channel_manager.free_channel(self.target_fgc, PROTOCOL_NAME, self.target_gw)
                self.channel = None
                raise RuntimeError(f"Could not set token on gateway {self.target_gw}: {e}") from e

            else:
                self.channel.token_set = True

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

    def renew_token(self, token):
        self.rbac_token = token
        self._set_token()
        
    def _set_token(self):
        if self.rbac_token is None:
            logger.warning(f"Received None token for gateway {self.target_gw}. Token not set.")
            return

        prop = "CLIENT.TOKEN"
        set_command = cmd.parse_set(self.target_gw, PROTOCOL_NAME, prop, value=self.rbac_token)

        try:
            self.channel.write(set_command)

        except Exception as e:
            raise RuntimeError(f"ERROR (set) for device {self.target_gw}, property {prop}: {e}") from e

        try:
            self._receive()

        except Exception as e:
            raise RuntimeError(f"ERROR parsing response for device {self.target_gw}, property {prop}: {e}") from e
    
    def _receive(self):
        response = list()

        received = self.channel.read(1)
        while received not in [rsp.NET_RSP_VOID, rsp.NET_RSP_END, rsp.NET_RSP_BIN_FLAG]:
            response.append(received)
            received = self.channel.read(1)

        response.append(received)

        # Binary response
        if received == rsp.NET_RSP_BIN_FLAG:
            response_length_bytes = self.channel.read(4)
            response.append(response_length_bytes)

            # Format string !L -> ! (network = big endian), L (unsigned long)
            # Length read from the payload + 2 characters for the '\n;' in the end
            response_length_int = struct.unpack('!L', response_length_bytes)[0] + 2

            byte_counter = 0
            while byte_counter < response_length_int:
                incoming_bytes = self.channel.read(response_length_int - byte_counter)
                byte_counter += len(incoming_bytes)
                response.append(incoming_bytes)

        byte_rsp = b"".join(response)
        return byte_rsp

    def _command_engine(self, prop, command_encoder, cmd_argument):
        response_dict   = dict()
        encoded_command = command_encoder(self.target_fgc, "sync", prop, cmd_argument)
        with self.channel.lock:
            try:
                self.channel.write(encoded_command)

            except Exception as e:
                raise RuntimeError(f"Exception while sending command {encoded_command} to fgc {self.target_fgc}") from e

            try:
                response_dict[self.target_fgc] = self._receive()

            except Exception as e:
                raise RuntimeError(f"Exception while receiving response to command {encoded_command.decode()}: {repr(e)}, {traceback.print_exc()}") from e

        return rsp.FgcResponse(PROTOCOL_NAME, response_dict)

