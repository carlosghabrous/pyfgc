from contextlib import contextmanager

from .fgc_session   import FgcSession
from .fgc_response  import FgcResponse
from .fgc_monitor   import Monitor
from .fgc_terminal  import RemoteTerminal


@contextmanager
def fgcs(targets, protocol="sync", **kwargs):
    fgc_session = None

    try:
        fgc_session = FgcSession(targets, protocol, **kwargs)
        yield fgc_session
    #TODO: try to use a more concrete exception type
    except Exception as e:
        raise PyFgcError(f"Exception in pyfgc context manager: {e}")

    finally:
        if fgc_session:
            disconnect(fgc_session)
    

def connect(targets, protocol="sync", **kwargs):
    fgc_session = None

    try:
        fgc_session = FgcSession(targets, protocol, **kwargs)
    
    #TODO: try to use a more concrete exception type
    except Exception as e:
        raise PyFgcError(f"Error building FgcSession for targets {targets}, protocol {protocol}: {e}")

    else:
        return fgc_session


def disconnect(fgc_session, targets=None):
    fgc_session.disconnect(targets=targets)


def get(targets, prop, get_option=None, protocol="sync", **kwargs):
    with fgcs(targets, protocol=protocol, **kwargs) as fgc_session:
        return fgc_session.get(prop, get_option)


def set(targets, prop, value, protocol="sync", **kwargs):
    with fgcs(targets, protocol, **kwargs) as fgc_session:
        return fgc_session.set(prop, value)


def monitor(targets, callback, **kwargs):
    return Monitor(targets, callback, **kwargs)


def terminal(targets, callback, **kwargs):
    return RemoteTerminal(targets, callback, **kwargs)

class PyFgcError(Exception):
    pass
    
