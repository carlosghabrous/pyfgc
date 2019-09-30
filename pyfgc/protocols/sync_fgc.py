import builtins
import socket
import struct

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

# sync_logger = get_pyfgc_logger(__name__)

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

    # Eliminate duplicated gateways if several targets are behind the same one
    gws = {pyfgc_name.devices[d.upper()]["gateway"] for d in targets}
    for gw in gws:
        global available_connections
        if not gw in available_connections.keys():
            gw_devices = pyfgc_name.gateways[gw]["devices"]

            available_connections[gw] = dict()
            available_connections[gw]["devices"] = gw_devices
            available_connections[gw]["socket"]  = None

            try:
                s = socket.socket()
                s.settimeout(timeout_s)
                s.connect((gw, PORT))

            except Exception as e:
                print(f"Could not open socket with gw {gw}: {e}")
                continue
            
            available_connections[gw]["socket"] = s

            try:
                _handshake(s, gw)
                _set_token(rbac_token, gw, s)

            except Exception as e:
                s.close()
                s = None
                continue    

def get(prop, get_option=None, targets=None):
    """[summary]
    
    [description]
    
    Arguments:
        prop {[type]} -- [description]
    
    Keyword Arguments:
        targets {[type]} -- [description] (default: {None})
    
    Returns:
        [type] -- [description]
    """
    return _command_engine(targets, prop, cmd.parse_get, cmd_argument=get_option)


def set(prop, value, targets=None):
    """[summary]
    
    [description]
    
    Arguments:
        prop {[type]} -- [description]
        value {[type]} -- [description]
    
    Keyword Arguments:
        targets {[type]} -- [description] (default: {None})
    
    Returns:
        [type] -- [description]
    """

    return _command_engine(targets, prop, cmd.parse_set, cmd_argument=value)
            

def disconnect(targets=None):
    """[summary]
    
    [description]
    
    Keyword Arguments:
        targets {[type]} -- [description] (default: {None})
    """
        
   
    global target_set
    # Disconnect from selected targets or all target_set
    remove_devices = targets and targets or list(target_set)

    # Update target set for future operations
    target_set = target_set - builtins.set(remove_devices)
    
    # Sockets are closed only if no targets are specified (disconnect from all)
    if not targets:
        global available_connections
        for gw in available_connections.keys():
            s = available_connections[gw]["socket"]
            try:
                s.close()
            except:
                pass

            available_connections[gw]["socket"] = None

        available_connections.clear()


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


def _handshake(s, gw):

    if s.recv(1) != b"+":
        raise ConnectionError("Handshake with gateway {} not successful!".format(gw))

    else:
        s.sendall(b"+")


def _set_token(token, gw, channel):
    """[summary]
    
    [description]
    
    Arguments:
        token {[type]} -- [description]
        gw {[type]} -- [description]
        channel {[type]} -- [description]
    """ 

    if token is None:
        return
        
    prop = "CLIENT.TOKEN"
    set_command = cmd.parse_set(gw, "sync", prop, value=token)

    try:
        channel.sendall(set_command)

    except Exception as e:
        print(f"ERROR (set) for device {gw}, property {prop}: {e}")
        raise

    try:
        _receive(channel)

    except Exception as e:
        print(f"ERROR parsing response for device {gw}, property {prop}: {e}")
        raise


def _receive(channel):
    response = list()

    received = channel.recv(1)
    while received not in [rsp.NET_RSP_VOID, rsp.NET_RSP_END, rsp.NET_RSP_BIN_FLAG]:
        response.append(received)
        received = channel.recv(1)

    response.append(received)

    # Binary response
    if received == rsp.NET_RSP_BIN_FLAG:
        response_length_bytes = channel.recv(4)
        response.append(response_length_bytes)

        # Format string !L -> ! (network = big endian), L (unsigned long)
        # Length read from the payload + 2 characters for the '\n;' in the end
        response_length_int = struct.unpack('!L', response_length_bytes)[0] + 2

        byte_counter = 0
        while byte_counter < response_length_int:
            incoming_bytes = channel.recv(response_length_int - byte_counter)
            byte_counter += len(incoming_bytes)
            response.append(incoming_bytes)

    byte_rsp = b"".join(response)
    return byte_rsp


def _command_engine(targets, prop, command_encoder, cmd_argument):
    command_targets = _get_command_targets(targets)
    response_dict = dict()

    # global sync_logger
    for t in command_targets:
        encoded_command = command_encoder(t, "sync", prop, cmd_argument)
        gw = pyfgc_name.devices[t.upper()]["gateway"]

        try:
            channel = available_connections[gw]["socket"]
            channel.sendall(encoded_command)

        except Exception as e:
            # sync_logger.error(f"Device {t} could take action on property {prop}: {e}")
            continue

        try:
            response_dict[t] = _receive(channel)

        except Exception as e:
            # sync_logger.error(f"Did not receive response from device {t}: {e}")
            continue

    return rsp.FgcResponse(PROTOCOL_NAME, response_dict)
