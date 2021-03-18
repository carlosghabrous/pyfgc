"""Pyfgc API

This module provides several utilities to communicate with CERN's FGCs.
It abstracts the usage of several protocols such as SCRP, NCRP and UDP status
publication.

Pyfgc is compatible with python asyncio module.

Todo:
    * After upgrading from python 3.6 to 3.7/3.8, the asyncio implementation
    should be revisited, to adopt the new (better) features provided by these
    releases.
    * After upgrading from python 3.6 to 3.7/3.8, replace asyncio.get_event_loop
    by asyncio.get_running_loop.
    * fgc terminal module is not yet implemented.
    * Unify FgcResponse and FgcSingleResponse classes as a single one.
"""
from contextlib import contextmanager
from typing import Callable, Dict, List

from .fgc_session   import FgcSession, FgcAsyncSession
from .fgc_monitor   import MonitorSession, MonitorPort
from .fgc_terminal  import RemoteTerminal

# Synchronous functions

@contextmanager
def fgc(target: str, protocol: str = "sync", **kwargs):
    """Synchonous context manager

    Context manager that handles the creation/destruction of a synchrounous fgc
    session.

    Depending on the protocol, the connection channel may be shared between
    different sessions.

    Args:
        target (str): Target fgc name.
        protocol (str, optional): Communication protocol (sync/serial). Defaults
            to sync.
        **kwargs: Arbitrary keyword arguments:
            {
                name_file (str): Path/url to name file.
                rbac_token (bytes): CERN rbac token. Pass None to disable rbac.
                timeout_s (float): Timeout in seconds.
            }

    Returns:
        FgcSession: fgc session object
    """
    fgc_session = None

    try:
        fgc_session = FgcSession(target, protocol, **kwargs)

    except Exception as err:
        raise PyFgcError(f"Exception in pyfgc context manager: {err}") from err

    else:
        yield fgc_session

    finally:
        if fgc_session:
            disconnect(fgc_session)

def connect(target: str, protocol: str = "sync", **kwargs):
    """Open connection to a device

    Args:
        target (str): Target fgc name.
        protocol (str, optional): Communication protocol (sync/serial). Defaults
            to sync.
        **kwargs: Arbitrary keyword arguments:
            {
                name_file (str): Path/url to name file.
                rbac_token (bytes): CERN rbac token. Pass None to disable rbac.
                timeout_s (float): Timeout in seconds.
            }

    Returns:
        FgcSession: fgc session object
    """
    fgc_session = None

    try:
        fgc_session = FgcSession(target, protocol, **kwargs)

    # TODO: try to use a more concrete exception type
    except Exception as err:
        raise PyFgcError(f"Error building FgcSession for target {target}, "
                         f"protocol {protocol}: {err}") from err
    else:
        return fgc_session

def disconnect(fgc_session: FgcSession) -> None:
    """Close connection to a device

    Args:
        fgc_session (FgcSession): Fgc session to close.
    """
    fgc_session.disconnect()

def get(target: str, prop: str, get_option: str = None, protocol: str = "sync", **kwargs):
    """Get a device property

    Does not require the explicit creation of a session.
    However, it has a bigger overhead (session is created and destroyed internally).

    Args:
        target (str): Target fgc name.
        prop (str): Property to get.
        get_option (str, optional): Get option.
        protocol (str, optional): Communication protocol (sync/serial). Defaults
            to sync.
        **kwargs: Arbitrary keyword arguments:
            {
                name_file (str): Path/url to name file.
                rbac_token (bytes): CERN rbac token. Pass None to disable rbac.
                timeout_s (float): Timeout in seconds.
            }

    Returns:
        FgcResponse: FGC response object
    """
    with fgc(target, protocol=protocol, **kwargs) as fgc_session:
        return fgc_session.get(prop, get_option)

# TODO: This is overriding the keyword set()!
def set(target: str, prop: str, value: str, protocol: str = "sync", **kwargs):
    """Set a device property

    Does not require the explicit creation of a session.
    However, it has a bigger overhead (session is created and destroyed internally).

    Args:
        target (str): Target fgc name.
        prop (str): Property to set.
        value (str): New value.
        protocol (str, optional): Communication protocol (sync/serial). Defaults
            to sync.
        **kwargs: Arbitrary keyword arguments:
            {
                name_file (str): Path/url to name file.
                rbac_token (bytes): CERN rbac token. Pass None to disable rbac.
                timeout_s (float): Timeout in seconds.
            }

    Returns:
        FgcResponse: FGC response object
    """
    with fgc(target, protocol=protocol, **kwargs) as fgc_session:
        return fgc_session.set(prop, value)

# Asynchronous functions (asyncio coroutines)

class async_fgc:
    """Asynchonous context manager

    Async context manager that handles the creation/destruction of an asynchrounous fgc
    session.

    The connection channel may be shared between different sessions.

    Args:
        target (str): Target fgc name.
        protocol (str, optional): Communication protocol (async/...). Defaults
            to async.
        loop (AbstractEventLoop, optional): Asyncio event loop. If not defined,
            the current event loop will be used.
        **kwargs: Arbitrary keyword arguments:
            {
                name_file (str): Path/url to name file.
                rbac_token (bytes): CERN rbac token. Pass None to disable rbac.
                timeout_s (float): Timeout in seconds.
            }

    Returns:
        FgcAsyncSession: fgc session object
    """
    # TODO: Replace this class by a function with @asynccontextmanager decorator, in python 3.7.
    def __init__(self, target: str, protocol: str = "async", loop=None, **kwargs):
        self._target = target
        self._protocol = protocol
        self._loop = loop
        self._kwargs = kwargs
        self.asyn_session = None

    async def __aenter__(self):
        self.asyn_session = await async_connect(
            self._target, self._protocol, loop=self._loop, **self._kwargs)
        return self.asyn_session

    async def __aexit__(self, exc_type, exc, tb):
        if self.asyn_session:
            await async_disconnect(self.asyn_session)

async def async_connect(target: str, protocol: str = "async", loop=None, **kwargs):
    """Open async connection to a device

    Args:
        target (str): Target fgc name.
        protocol (str, optional): Communication protocol (async/...). Defaults
            to async.
        loop (AbstractEventLoop, optional): Asyncio event loop. If not defined,
            the current event loop will be used.
        **kwargs: Arbitrary keyword arguments:
            {
                name_file (str): Path/url to name file.
                rbac_token (bytes): CERN rbac token. Pass None to disable rbac.
                timeout_s (float): Timeout in seconds.
            }

    Returns:
        FgcAsyncSession: fgc session object
    """
    fgc_session = None

    try:
        fgc_session = await FgcAsyncSession.instance(target, protocol, loop, **kwargs)

    # TODO: try to use a more concrete exception type
    except Exception as err:
        raise PyFgcError(f"Error building FgcSession for target {target}, "
                         f"protocol {protocol}: {err}") from err
    else:
        return fgc_session

async def async_disconnect(fgc_session: FgcAsyncSession) -> None:
    """Close async connection to a device

    Args:
        fgc_session (FgcAsyncSession): Fgc session to close.
    """
    await fgc_session.disconnect()

async def async_get(target: str, prop: str, get_option=None, protocol="async", loop=None, **kwargs):
    """Get a device property asynchronously

    Does not require the explicit creation of a session.
    However, it has a bigger overhead (session is created and destroyed internally).

    Args:
        target (str): Target fgc name.
        prop (str): Property to get.
        get_option (str, optional): Get option.
        protocol (str, optional): Communication protocol (async/...). Defaults
            to async.
        loop (AbstractEventLoop, optional): Asyncio event loop. If not defined,
            the current event loop will be used.
        **kwargs: Arbitrary keyword arguments:
            {
                name_file (str): Path/url to name file.
                rbac_token (bytes): CERN rbac token. Pass None to disable rbac.
                timeout_s (float): Timeout in seconds.
            }

    Returns:
        FgcSingleResponse: FGC response object
    """
    async with async_fgc(target, protocol, loop, **kwargs) as fgc_session:
        return await fgc_session.get(prop, get_option)

async def async_set(target: str, prop: str, value, protocol="async", loop=None, **kwargs):
    """Set a device property asynchronously

    Does not require the explicit creation of a session.
    However, it has a bigger overhead (session is created and destroyed internally).

    Args:
        target (str): Target fgc name.
        prop (str): Property to set.
        value (str): New value.
        protocol (str, optional): Communication protocol (async/...). Defaults
            to async.
        loop (AbstractEventLoop, optional): Asyncio event loop. If not defined,
            the current event loop will be used.
        **kwargs: Arbitrary keyword arguments:
            {
                name_file (str): Path/url to name file.
                rbac_token (bytes): CERN rbac token. Pass None to disable rbac.
                timeout_s (float): Timeout in seconds.
            }

    Returns:
        FgcSingleResponse: FGC response object
    """
    async with async_fgc(target, protocol, loop, **kwargs) as fgc_session:
        return await fgc_session.set(prop, value)

# Monitor

def monitor_session(callback: Callable[[Dict, List, str, float], None],
                    targets, period, timeout: float = None, callback_err=None,
                    **kwargs):
    """Subscribe to FGC published properties.

    Opens a session to one (or more) FGC gateway, and subscribes to its published
    properties.
    Callback will be invoked everytime a new UDP packet is received.

    Can be used as a context manager.
    Alternativelly, can be started with self.start() and stopped with self.stop().

    Args:
        callback (Callable): Callback that will be invoked when new data is
            received.
        targets (List): List of targets to monitor.
        period (int): Subcribed data refresh period.
        timeout (float, optional): Timeout for subcribed data (in seconds).
        callback_err (Callable, optional): Extra callback that will be invoked
            when there was an exception during the original callback execution.
        **kwargs: Arbitrary keyword arguments:
            {
                name_file (str): Path/url to name file.
                rbac_token (bytes): CERN rbac token. Pass None to disable rbac.
            }

    callback arguments:
        Dict: Dictionary mapping device names to dictionaries of published
            properties.
        {
            <device_name (str)>: {
                <property_name (str)>: <property_value>,
                ...
            },
            ...
        }
        List: Array of 64 iterm, mapping device positions [0..64] to dictionaries
            of published properties.
        [
            {
                <property_name (str)>: <property_value>,
                ...

            }, # Device 0
            {
                ...
            }, # Device 1
            ...
            {
                ...
            }  # Device 64
        ]
        str: Name (address) of gateway that sent current data fields.
        float: Timestamp of current data, as reported by the gateway.

    callback_err arguments:
        Exception: Excpetion that triggered the callback invocation.
        str: Name (address) of gateway associated with the exception. Or None.
        float: Current timestamp.

    Returns:
        MonitorSession: FGC monitor session object
    """
    return MonitorSession(callback,
                          targets,
                          period,
                          timeout=timeout,
                          callback_err=callback_err,
                          **kwargs)

def monitor_port(callback: Callable[[Dict, List, str, float], None],
                 sub_port: int, filter_address=None, filter_id=None,
                 timeout: float = None, callback_err=None, **kwargs):
    """Listen to FGC published properties at a port

    Callback will be invoked everytime a new UDP packet is received.
    This should be used when the gateway are sending the published data
    to a fixed IP (of the current machine), without requiring a session.

    Can be used as a context manager.
    Alternativelly, can be started with self.start() and stopped with self.stop().

    Args:
        callback (Callable): Callback that will be invoked when new data is
            received.
        sub_port (int): Port to listen for UDP data.
        filter_address (List[str], optional): only accept data from these
            addresses.
        filter_id (List[int], optional): only accept data with this ID token.
        timeout (float, optional): Timeout for subcribed data (in seconds).
        callback_err (Callable, optional): Extra callback that will be invoked
            when there was an exception during the original callback execution.
        **kwargs: Arbitrary keyword arguments:
            {
                name_file (str): Path/url to name file.
                rbac_token (bytes): CERN rbac token. Pass None to disable rbac.
            }

    callback arguments:
        Dict: Dictionary mapping device names to dictionaries of published
            properties.
        {
            <device_name (str)>: {
                <property_name (str)>: <property_value>,
                ...
            },
            ...
        }
        List: Array of 64 iterm, mapping device positions [0..64] to dictionaries
            of published properties.
        [
            {
                <property_name (str)>: <property_value>,
                ...

            }, # Device 0
            {
                ...
            }, # Device 1
            ...
            {
                ...
            }  # Device 64
        ]
        str: Name (address) of gateway that sent current data fields.
        float: Timestamp of current data, as reported by the gateway.

    callback_err arguments:
        Exception: Excpetion that triggered the callback invocation.
        str: Name (address) of gateway associated with the exception. Or None.
        float: Current timestamp.

    Returns:
        MonitorPort: FGC monitor port object
    """
    return MonitorPort(callback,
                       sub_port,
                       filter_address=filter_address,
                       filter_id=filter_id,
                       timeout=timeout,
                       callback_err=callback_err,
                       **kwargs)

# FGC terminal

# TODO:
def terminal(target: str, callback: Callable, **kwargs):
    return RemoteTerminal(target, callback, **kwargs)

# TODO:
class PyFgcError(Exception):
    pass



# EOF
