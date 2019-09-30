from contextlib import contextmanager
import importlib

import pyfgc_name
import pyfgc_rbac

_protocol_module = None
_auth_token = None

@contextmanager
def fgcs(targets, proto, **kwargs):
    """[summary]
    
    [description]
    
    Decorators:
        contextmanager
    
    Arguments:
        targets {[type]} -- [description]
        proto {[type]} -- [description]
        **kwargs {[type]} -- [description]
    
    Yields:
        [type] -- [description]
    """

    try:
        _connections = connect(targets, proto, **kwargs)
        yield _connections

    except:
        raise

    finally: 
        disconnect()


def connect(targets, proto, **kwargs):
    """[summary]
    
    [description]
    
    Arguments:
        targets {[type]} -- [description]
        proto {[type]} -- [description]
        **kwargs {[type]} -- [description]
    
    Returns:
        [type] -- [description]
    """

    # Get name file from argument or default 
    try:
        name_file = kwargs["name_file"]

    except KeyError:
        pyfgc_name.read_name_file()

    else:
        pyfgc_name.read_name_file(name_file)

    # Get RBAC token from argument or try get by location. If location fails, it is set to None
    global _auth_token
    try:
        _auth_token = kwargs["rbac_token"]

    except KeyError:
        _auth_token = _get_token()

    # Get timeout. TODO: necessary?
    timeout_s = kwargs.get("timeout_s", None)
      

    global _protocol_module
    _protocol_module = _get_protocol_module(proto)

    target_list = (proto == "serial") and targets or pyfgc_name.build_device_set(targets)
    if not target_list:
        raise RuntimeError(f"Did not find devices named like {targets}, or devices were empty")

    try:
        return _protocol_module.connect(target_list, _auth_token, timeout_s=timeout_s)  

    except AttributeError:
        print("Protocol module {} has no connect function".format(proto))        
        raise 


def get(prop, **kwargs):
    """[summary]
    
    [description]
    
    Arguments:
        prop {[type]} -- [description]
        **kwargs {[type]} -- [description]
    
    Returns:
        [type] -- [description]
    """

    # client may specify subset of devices to which apply the command

    devices = kwargs.get("devices", None)
    protocol = kwargs.get("protocol", None)
    get_option = kwargs.get("get_option", None)
    
    if _protocol_module is not None: 
        return _protocol_module.get(prop, get_option=get_option, devices=pyfgc_name.build_device_set(devices))

    else:
        with fgcs(devices, protocol, **kwargs):
            return _protocol_module.get(prop, get_option=get_option)


def set(prop, value, **kwargs):
    """[summary]
    
    [description]
    
    Arguments:
        prop {[type]} -- [description]
        value {[type]} -- [description]
        **kwargs {[type]} -- [description]
    
    Returns:
        [type] -- [description]
    """

    devices = kwargs.get("devices", None)
    protocol = kwargs.get("protocol", None)

    if _protocol_module is not None:
        return _protocol_module.set(prop, value, devices=pyfgc_name.build_device_set(devices))

    else:
        with fgcs(devices, protocol, **kwargs):
            return _protocol_module.set(prop, value)
    
    
def subscribe(props, callback, period, **kwargs):
    """[summary]
    
    [description]
    
    Arguments:
        props {[type]} -- [description]
        callback {function} -- [description]
        period {[type]} -- [description]
        **kwargs {[type]} -- [description]
    
    Raises:
        NotImplementedError -- [description]
    """

    raise NotImplementedError


def status_monitor(filter, action, **kwargs):
    pass
 

def disconnect(devices=None):
    """[summary]
    
    [description]
    
    Keyword Arguments:
        devices {[type]} -- [description] (default: {None})
    """

    global _protocol_module

    _protocol_module.disconnect(pyfgc_name.build_device_set(devices))
    
    if not _protocol_module.has_open_connections():
        _protocol_module = None


def _get_protocol_module(protocol):
    """[summary]
    
    [description]
    
    Arguments:
        protocol {[type]} -- [description]
    
    Returns:
        [type] -- [description]
    """

    try:
        return importlib.import_module("pyfgc.protocols." + protocol)

    except TypeError:
        print("protocol {} is not a string".format(repr(protocol)))

    except ModuleNotFoundError:
        print("FGC protocol {} module not found!".format(protocol))
        raise

def _get_token():

    try:
        return pyfgc_rbac.get_token_location()

    except Exception:
        return None
