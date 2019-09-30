import builtins
import struct

import serial

import pyfgc.parsers.command as cmd
import pyfgc.fgc_response as rsp

# Constants
CONNECTION_TIMEOUT = 1
PROTOCOL_NAME = __name__.rsplit(".")[-1].split("_")[0]


_serial_channel = None

try:
    target_set

except NameError:
    target_set = builtins.set()


class SCRPNonPrintable(object):
    SCRP_ABORT_GET = b"\x03"
    SCRP_EXECUTE_CMD_LF = b"\x0A"
    SCRP_EXECUTE_CMD_CR = b"\x0D"
    SCRP_RESUME_TX = b"\x11"
    SCRP_SUSPEND_TX = b"\x13"
    SCRP_SWITCH_DIRECT = b"\x1A"
    SCRP_SWITCH_EDITOR = b"\x1B"


def connect(targets, auth_token=None, timeout_s=CONNECTION_TIMEOUT):
    """
    """    

    target_port = targets.pop()

    global target_set
    target_set.add(target_port)

    global _serial_channel
    if _serial_channel is not None and _serial_channel.isOpen():
        return

    try:
        _serial_channel = serial.Serial(target_port, timeout=CONNECTION_TIMEOUT)

    except serial.SerialException as e:
        raise Exception("{}".format(e)) from e

    else:
        _set_mode(SCRPNonPrintable.SCRP_SWITCH_DIRECT)
        return target_set


def disconnect(targets=None):
    """
    """

    global _serial_channel
    try:
        _serial_channel.close()

    except AttributeError:
        pass

    finally:
        global target_set
        target_set.clear()
        _serial_channel = None


def get(prop, get_option=None, targets=None):
    """
    @brief      { function_description }
    
    @param      prop        The property
    @param      get_option  The get option
    
    @return     { description_of_the_return_value }
    """

    return _command_engine(prop, cmd.parse_get, cmd_argument=get_option)

def set(prop, value, targets=None):
    """
    @brief      { function_description }
    
    @param      prop   The property
    @param      value  The value
    
    @return     { description_of_the_return_value }
    """

    return _command_engine(prop, cmd.parse_set, cmd_argument=value)

def has_open_connections():
    """
    @brief      Determines if it has open connections.
    
    @return     True if has open connections, False otherwise.
    """
    return _serial_channel is not None

def _set_mode(mode):

    try:
        _serial_channel.write(mode)

    except serial.SerialException as s:
        raise ("Could not set terminal mode to {}: {}".format(mode, s)) from s


def _receive(channel):

    response = list()

    received = channel.read(size=1)
    while received not in [rsp.NET_RSP_VOID, rsp.NET_RSP_END, rsp.NET_RSP_BIN_FLAG]:
        response.append(received)
        received = channel.read(size=1)

    response.append(received)

    # Binary response
    if received == rsp.NET_RSP_BIN_FLAG:
        response_length_bytes = channel.read(4)
        response.append(response_length_bytes)

        # Format string !L -> ! (network = big endian), L (unsigned long)
        response_length_int = struct.unpack("!L", response_length_bytes)[0]

        byte_counter = 0
        while byte_counter < response_length_int:
            incoming_bytes = channel.read(response_length_int)
            byte_counter += len(incoming_bytes)
            response.append(incoming_bytes)

    byte_rsp = b"".join(response)
    return byte_rsp


def _command_engine(prop, command_encoder, cmd_argument):

    response_dict = dict()

    encoded_command = command_encoder("", "serial", prop, cmd_argument)

    global _serial_channel
    try:
        _serial_channel.write(encoded_command)

    except serial.SerialException as e:
        print("ERROR (get) for device {}: {}".format(t, e))
        raise
        
    response_dict[_serial_channel.name] = _receive(_serial_channel)
    return rsp.FgcResponse(PROTOCOL_NAME, response_dict)
