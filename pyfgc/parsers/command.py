import struct

NET_END = b"\n"
SER_END = b"\n"

_protocol_cmd_parsers = dict()


# API
def parse_set(device, protocol, prop, value=None, tag=None):

    global _protocol_cmd_parsers
    cmd_parser = _protocol_cmd_parsers[protocol][0]
    return cmd_parser(device, prop, value, tag)


def parse_get(device, protocol, prop, get_option=None, tag=None):

    global _protocol_cmd_parsers
    cmd_parser = _protocol_cmd_parsers[protocol][1]
    return cmd_parser(device, prop, get_option, tag)


# SERIAL 
def _parse_set_serial(device, prop, value, tag=None):

    command_init_bytes = "! S {}".format(prop).encode()
    value_bytes = _encode_value(value)

    return command_init_bytes + " ".encode() + value_bytes + SER_END


def _parse_get_serial(device, prop, get_option, tag=None):

    command_init_bytes = "! G {}".format(prop).encode()
    option_bytes = get_option and get_option.encode() or "".encode()

    return command_init_bytes + " ".encode() + option_bytes + SER_END


# NET SYNC and ASYNC
def _parse_set_net(device, prop, value, tag=None):
    
    command_tag = (tag is not None) and tag or ""

    command_init_bytes = "!{} S {}:{}".format(command_tag, device, prop).encode()
    value_bytes = _encode_value(value)

    return command_init_bytes + " ".encode() + value_bytes + NET_END


def _parse_get_net(device, prop, get_option, tag=None):

    command_tag = (tag is not None) and tag or ""

    command_init_bytes = "!{} G {}:{}".format(command_tag, device, prop).encode()
    option_bytes = get_option and get_option.encode() or "".encode()

    return command_init_bytes + " ".encode() + option_bytes + NET_END


# COMMON 
_protocol_cmd_parsers = {
    "serial": (_parse_set_serial, _parse_get_serial),
    "sync"  : (_parse_set_net,    _parse_get_net,  ), 
    "async" : (_parse_set_net,    _parse_get_net,  )
    }

def _encode_value(value):

    # string
    if isinstance(value, str):
        return value.encode()

    # bytes: case for the CLIENTS.TOKEN property
    if isinstance(value, bytes):
        return struct.pack('!BL', 255, len(value)) + value

    # list
    if hasattr(value, '_getitem_'):

        str_list = [str(item) for item in value]
        return ",".join(str_list).encode()

    # numbers, other data types
    return str(value).encode()
