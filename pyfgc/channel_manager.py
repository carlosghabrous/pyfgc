import asyncio
import random
import socket
import threading
from collections import namedtuple
from enum import Enum

import serial

# Enum to define channel types and helper to translate strings into enum members
class ChannelTypes(Enum):
    SYNC      = "sync"
    ASYNC     = "async"
    SERIAL    = "serial"
    TERMINAL  = "terminal"
    MONITOR   = "monitor"

def _channel_type_enum_from_string(channel_type):
    try:
        chan_type = ChannelTypes[channel_type.upper()]

    except KeyError:
        raise NotImplementedError(f"Channel of type {channel_type} not implemented!")

    else:
        return chan_type

# Helper to get the data from a channel in a structured way
ChannelData = namedtuple("ChannelData", "clients, channel_ref_count, channel")

class SyncChannel:
    PORT      = 1905
    TIMEOUT_S = 60

    def __init__(self, device, port=PORT, timeout_s=TIMEOUT_S):
        self.device = device
        self.port   = port
        self.lock   = threading.Lock()
        self.socket = socket.socket()
        
        self.socket.settimeout(timeout_s)

        self.create()
        
    def create(self):
        try:
            self.socket.connect((self.device, self.port))

        except socket.timeout as ste:
            raise (ste)
            
        with self.lock:
            try:
                self._do_handshake()

            except Exception as e:
                if self.socket:
                    self.socket.close()
                    raise RuntimeError(f"Could not complete handshake with device {self.device}: {e}")                

    def read(self, n_bytes):
        return self.socket.recv(n_bytes)

    def write(self, message):
        self.socket.sendall(message)

    def destroy(self):
        if self.socket:
            try:
                self.socket.close()

            except Exception as e:
                raise(e)

    def _do_handshake(self):
        if self.socket.recv(1) != b"+":
            raise ConnectionError(f"Handshake with gateway {self.device} not successful!")

        else:
            self.socket.sendall(b"+")

class AsyncChannel:
    PORT = 1905

    def __init__(self, device, port=PORT):
        self.device = device
        self.port   = port
        self.reader, self.writer = None, None

    async def create(self):
        self.reader, self.writer = await asyncio.open_connection(self.device, self.port)

    async def read(self, n_bytes):
        await self.reader.read(n_bytes)

    def write(self, message):
        binary_message = message.encode() if not isinstance(message, bytes) else message
        self.writer.write(binary_message)

    async def drain(self):
        await self.writer.drain() 

    def destroy(self):
        self.writer.close()

class MonitorChannel:
    def __init__(self, device):
        pass

    def create(self):
        pass

    def read(self):
        pass

    def write(self):
        pass

    def destroy(self):
        pass

class SerialChannel:

    class SCRPNonPrintable(object):
        SCRP_ABORT_GET = b"\x03"
        SCRP_EXECUTE_CMD_LF = b"\x0A"
        SCRP_EXECUTE_CMD_CR = b"\x0D"
        SCRP_RESUME_TX = b"\x11"
        SCRP_SUSPEND_TX = b"\x13"
        SCRP_SWITCH_DIRECT = b"\x1A"
        SCRP_SWITCH_EDITOR = b"\x1B"
    
    TIMEOUT_S = 60

    def __init__(self, device):
        self.device = device
        self.lock   = threading.Lock()
        self.serial_channel = None

        self.create()

    def create(self):
        try:
            self.serial_channel = serial.Serial(self.device, timeout=SerialChannel.TIMEOUT_S)

        except serial.SerialException as se:
            raise RuntimeError(f"Could not connect to serial port {self.device}: {se}")

        else:
            self._set_mode(SerialChannel.SCRPNonPrintable.SCRP_SWITCH_DIRECT)
            return self.serial_channel

    def read(self, n_bytes):
        return self.serial_channel.read(n_bytes)

    def write(self, message):
        self.serial_channel.write(message)

    def destroy(self):
        if self.serial_channel:
            try:
                self.serial_channel.close()
                
            except Exception:
                pass

    def _set_mode(self, mode):
        try:
            self.serial_channel.write(mode)

        except serial.SerialException as se:
            raise RuntimeError(f"Could not set terminal mode to {mode} on fgc {self.device}: {se}")     

class TerminalChannel:
    def __init__(self, device):
        pass

    def read(self):
        pass

    def write(self):
        pass

    def destroy(self):
        pass

class ChannelFactory:
    @staticmethod
    def create(channel_type, device):
        return globals()[channel_type.value.capitalize() + "Channel"](device)

class GwSingleChannel:
    def __init__(self, *args, **kwargs):
        self.fgc, self.type, self.gateway = args
        self.channel       = None
        self.ref_count     = 0

        self._init_gw_channel(self.fgc, self.type, self.gateway)

    def _init_gw_channel(self, fgc, channel_type, gateway):
        device = fgc if channel_type == ChannelTypes.SERIAL else gateway

        try:
            self.channel = ChannelFactory.create(channel_type, device)

        except Exception:
            self.channel.destroy()
            self.channel = None

    def close(self, channel_type):
        self.channel.destroy()

    def __repr__(self):
        return f"ref_count: {self.ref_count}, channel: {self.channel}"

class FgcToGwChannelMap:
    def __init__(self, *args, **kwargs):
        self.fgc, self.type, self.gateway = args
        self._fgc_to_gw_channel = dict()
        self._fgc_to_clients    = dict()

        self._fgc_to_clients[self.fgc] = 0
        self._add_fgc_to_map(self.fgc, self.type, self.gateway)

    def _add_fgc_to_map(self, fgc, channel_type, gateway):
        if channel_type in [ChannelTypes.SYNC, ChannelTypes.ASYNC] and len(self._fgc_to_gw_channel):
            first_item_key = list(self._fgc_to_gw_channel.keys())[0]
            self._fgc_to_gw_channel[fgc] = self._fgc_to_gw_channel[first_item_key]

        else:
            self._fgc_to_gw_channel[fgc] = GwSingleChannel(fgc, channel_type, gateway)

        self._fgc_to_gw_channel[fgc].ref_count += 1
        self._fgc_to_clients[fgc]               = 1

    def update_data(self, fgc, channel_type, gateway):
        if fgc not in self._fgc_to_gw_channel:
            self._add_fgc_to_map(fgc, channel_type, gateway)

        else:
            self._fgc_to_clients[fgc] += 1

    def free_channel(self, fgc):
        self._fgc_to_clients[fgc] -= 1

        if self._fgc_to_clients[fgc] == 0:
            gw_channel = self._fgc_to_gw_channel[fgc]
            
            gw_channel.ref_count -= 1
            if gw_channel.ref_count == 0:
                gw_channel.close(self.type)
            
            del self._fgc_to_gw_channel[fgc]
            del self._fgc_to_clients[fgc]

    def __getitem__(self, fgc):
        channel_data = ChannelData(self._fgc_to_clients[fgc],
                self._fgc_to_gw_channel[fgc].ref_count,
                self._fgc_to_gw_channel[fgc].channel)

        return channel_data

    def __len__(self):
        return len(self._fgc_to_gw_channel)

    def __repr__(self):
        return "\n".join([f"fgc: {fgc}, clients: {self._fgc_to_clients[fgc]}, GwSingleChannel-> {gws}" for fgc, gws in self._fgc_to_gw_channel.items()])

class GwChannelTypes:
    def __init__(self, *args, **kwargs):
        self.fgc, self.type, self.gateway = args
        self._channel_types               = dict()

        self._add_channel(self.fgc, self.type, self.gateway)
    
    def _add_channel(self, fgc, channel_type, gateway):
        self._channel_types[channel_type] = FgcToGwChannelMap(fgc, channel_type, gateway)
        
    def update_data(self, fgc, channel_type, gateway):
        if channel_type not in self._channel_types:
            self._add_channel(fgc, channel_type, gateway)

        else:
            self._channel_types[channel_type].update_data(fgc, channel_type, gateway)

    def free_channel(self, channel_type, fgc):
        self._channel_types[channel_type].free_channel(fgc)
        if not len(self._channel_types[channel_type]):
            del self._channel_types[channel_type]

    def __getitem__(self, channel_type):
        return self._channel_types[channel_type]

    def __len__(self):
        return len(self._channel_types)

    def __repr__(self):
        return "\n".join([f"type: {channel_type}, FgcToChannelMap-> {ftcm}" for channel_type, ftcm in self._channel_types.items()])

class ChannelCollection:
    def __init__(self, *args, **kwargs):
        self._channels  = dict()
        self._lock      = threading.Lock()

    def add_channel(self, fgc, channel_type, gateway):
        with self._lock:
            if not gateway in self._channels:
                self._channels[gateway] = GwChannelTypes(fgc, channel_type, gateway)

            else:
                self._channels[gateway].update_data(fgc, channel_type, gateway)

        return self._channels[gateway][channel_type][fgc].channel

    def free_channel(self, fgc, channel_type, gateway):
        with self._lock:
            self._channels[gateway].free_channel(channel_type, fgc)

            if not len(self._channels[gateway]):
                del self._channels[gateway]

    def __getitem__(self, gateway):
        return self._channels[gateway]

    def __repr__(self):
        return "\n".join([f"gw: {gw}, GwTypeMap-> {gtm}" for gw, gtm in self._channels.items()])

try:
    _channel_collection

except NameError:
    _channel_collection = ChannelCollection()


def get_channel_data(fgc, channel_type, gateway):
    chan_type = _channel_type_enum_from_string(channel_type)

    channel_data = _channel_collection[gateway][chan_type][fgc]
    return channel_data

def free_channel(fgc, channel_type, gateway):
    chan_type_enum = _channel_type_enum_from_string(channel_type)
    _channel_collection.free_channel(fgc, chan_type_enum, gateway)

def get_channel(fgc, channel_type, gateway):
    chan_type_enum = _channel_type_enum_from_string(channel_type)        
    channel = _channel_collection.add_channel(fgc, chan_type_enum, gateway)
    return channel    
