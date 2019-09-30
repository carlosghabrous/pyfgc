import asyncio
import builtins
import socket
import struct
from collections import namedtuple

import pyfgc.parsers.command as cmd
import pyfgc.fgc_response as rsp
import pyfgc_name

# Constants
PORT = 1905
PROTOCOL_NAME = __name__.rsplit(".")[-1].split("_")[0]

# Globals
try:
    target_set

except NameError:
    target_set = builtins.set()

try:
    available_connections 

except NameError:
    available_connections = dict()

try:
    queued_commands

except NameError:
    queued_commands = dict()

tag              = 0
async_event_loop = None
AsyncCommand     = namedtuple("AsyncCommand", ["tag", "device", "prop", "future"])

def connect(targets, rbac_token, timeout_s):
    """[summary]
    
    [description]
    
    Arguments:
        targets {[type]} -- [description]
        rbac_token {[type]} -- [description]
    
    Keyword Arguments:
        timeout_s {[type]} -- [description] (default: {TIMEOUT_S})
    
    Returns:
        [type] -- [description]
    """

    global target_set
    target_set.update(targets)

    # Eliminate duplicates
    gws = {pyfgc_name.devices[d.upper()]["gateway"] for d in targets}

    for gw in gws:
        global available_connections
        if not gw in available_connections.keys():
            gw_devices = pyfgc_name.gateways[gw]["devices"]

            available_connections[gw] = dict()
            available_connections[gw]["devices"] = gw_devices

            global async_event_loop
            async_event_loop = asyncio.get_event_loop()
            if async_event_loop.is_closed():
                async_event_loop = asyncio.new_event_loop()

            streams = async_event_loop.run_until_complete(_create_stream(gw))
            available_connections[gw]["streams"] = streams

            try:
                async_event_loop.run_until_complete(_handshake(streams, gw))
                async_event_loop.run_until_complete(_set_token(rbac_token, gw, streams))

            except Exception as e:
                async_event_loop.run_until_complete(_close_stream(streams[1]))
                continue

async def _create_stream(gw):
    reader, writer = await asyncio.open_connection(gw, PORT)
    return reader, writer

async def _close_stream(writer_stream):
    writer_stream.close()
    # This line is needed in python 3.7
    # await writer_stream.wait_closed()

def get(prop, get_option=None, targets=None):
    return _command_engine(targets, prop, get_option, _async_get_single) 

def set(prop, value, targets=None):
    return _command_engine(targets, prop, value, _async_set_single)
            
def disconnect(targets=None):
    """[summary]
    
    [description]
    
    Keyword Arguments:
        targets {[type]} -- [description] (default: {None})
    """
    
    # Disconnect from selected targets or all targets   
    global target_set
    remove_targets = targets and targets or list(target_set)

    # Update target set for future operations
    target_set = target_set - builtins.set(remove_targets)
    
    # StreamWriters are closed only if no devices are specified (disconnect from all)
    if not targets:
        global async_event_loop
        global available_connections

        for gw in available_connections.keys():
            s = available_connections[gw]["streams"]

            try:
                async_event_loop.run_until_complete(_close_stream(s[1]))

            except Exception as e:
                print("Exception while closing streams: {}".format(e))

        available_connections.clear()

        try:
            async_event_loop.stop()
            async_event_loop.close()

        except Exception as e:
            print("Disconnect: {}".format(e))

def has_open_connections():
    return len(available_connections) != 0

def _get_command_targets(targets):
    """[summary]
    
    [description]
    
    Arguments:
        targets {[type]} -- [description]
    
    Returns:
        [type] -- [description]
    """
    global target_set
    cmd_targets = targets and [d for d in targets if d in target_set] or list(target_set)

    return cmd_targets

async def _handshake(streams, gw):
    reader, writer = streams
    data = await reader.read(1)

    if data != b"+":
        raise ConnectionError("Handshake with gateway {} not successful!".format(gw))

    else:
        writer.write(b"+")

async def _set_token(token, gw, streams):
    """[summary]
    
    [description]
    
    Arguments:
        token {[type]} -- [description]
        gw {[type]} -- [description]
        channel {[type]} -- [description]
    """ 
    if token is None:
        return
        
    reader, writer = streams
    prop = "CLIENT.TOKEN"
    tag, encoded_command = _build_command(gw, prop, token, cmd.parse_set)
    _push_command(tag, gw, prop)

    try:
        writer.write(encoded_command)

    except Exception as e:
        print("ERROR (set) for device {}, property {}: {}".format(gw, prop, e))
        raise

    try:
        await _get_response(reader, tag=tag)

    except Exception as e:
        print("ERROR parsing response for device {}, property {}: {}".format(gw, prop, e))
        raise

    finally: 
        _pop_command(tag)

async def _async_get_single(target, prop, get_option=None, lock=None):

    tag, encoded_command = _build_command(target, prop, get_option, cmd.parse_get)
    _push_command(tag, target, prop)

    gw = pyfgc_name.devices[target.upper()]["gateway"]

    try:
        reader, writer = available_connections[gw]["streams"]

        writer.write(encoded_command)
        await writer.drain()

        with await lock:
            await _get_response(reader)

    except Exception as e:
        print("ERROR (get) for device {}: {}".format(target, e))

async def _async_set_single(target, prop, value, lock=None):

    tag, encoded_command = _build_command(target, prop, value, cmd.parse_set)
    _push_command(tag, target, prop)

    gw = pyfgc_name.devices[target.upper()]["gateway"]

    try:
        reader, writer = available_connections[gw]["streams"]

        writer.write(encoded_command)
        await writer.drain()

        with await lock:
            await _get_response(reader)

    except Exception as e:
        print("ERROR (get) for device {}: {}".format(target, e))
    
async def _async_multiple_action(command_targets, prop, cmd_argument, single_action_coroutine):
    lock = asyncio.Lock()

    tasks = [asyncio.ensure_future(
        single_action_coroutine(target, prop, cmd_argument, lock)) 
        for target in command_targets]

    await asyncio.gather(*tasks)

    fgc_rsp = rsp.FgcResponse(PROTOCOL_NAME)
    global queued_commands

    # Make an explicit copy of the dictionary keys, as it is being changed during the iteration
    for tag in list(queued_commands.keys()):
        fgc_rsp[queued_commands[tag].device] = queued_commands[tag].future.result()
        _pop_command(tag)

    return fgc_rsp

def _command_engine(targets, prop, cmd_argument, single_action_coroutine):
    command_targets = _get_command_targets(targets)

    try:
        global async_event_loop  
        response = async_event_loop.run_until_complete(
            _async_multiple_action(
                command_targets, 
                prop, 
                cmd_argument, 
                single_action_coroutine))

    except Exception as e:
        print("Exception in command_engine: {}".format(e))
    response = rsp.FgcResponse(PROTOCOL_NAME)
    
    # Return dictionary if the command was issued to multiple targets
    return response

def _get_tag():
    import sys

    global tag
    cycle_tag = tag % sys.maxsize
    tag += 1
    return cycle_tag

def _build_command(target, prop, command_argument, encoder):
    command_tag = _get_tag()
    return command_tag, encoder(target, "async", prop, command_argument, command_tag)

def _push_command(command_tag, target, prop):
    global queued_commands
    command_future = asyncio.Future()
    queued_commands[command_tag] = AsyncCommand(command_tag, target, prop, command_future)

async def _get_response(s, tag=None):
    data = await _receive(s)
    fgc_single_rsp = rsp.FgcSingleResponse(PROTOCOL_NAME, data)

    command_tag = fgc_single_rsp.tag and int(fgc_single_rsp.tag) or tag
    global queued_commands
    try:
        q_command = queued_commands[command_tag]

    except KeyError:
        pass
    
    q_command.future.set_result(fgc_single_rsp)

def _pop_command(command_tag):

    global queued_commands    
    del queued_commands[command_tag]

async def _receive(channel):
    response = list()

    received = await channel.read(1)
    while received not in [rsp.NET_RSP_VOID, rsp.NET_RSP_END, rsp.NET_RSP_BIN_FLAG]:
        response.append(received)
        received = await channel.read(1)

    response.append(received)

    # Binary response
    if received == rsp.NET_RSP_BIN_FLAG:
        response_length_bytes = await channel.read(4)
        response.append(response_length_bytes)

        # Format string !L -> ! (network = big endian), L (unsigned long)
        response_length_int = struct.unpack('!L', response_length_bytes)[0]

        byte_counter = 0
        while byte_counter < response_length_int:
            incoming_bytes = await channel.read(response_length_int)
            byte_counter += len(incoming_bytes)
            response.append(incoming_bytes)

    byte_rsp = b"".join(response)
    return byte_rsp
