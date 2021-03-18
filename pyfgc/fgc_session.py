import asyncio
import concurrent.futures
import importlib
import logging
import time

import pyfgc_name
import pyfgc_rbac
from .fgc_response import FgcResponse

logger = logging.getLogger('pyfgc.fgc_session')
logger.setLevel(logging.INFO)

DEFAULT_TIMEOUT_S = 60.0

class FgcSession:
    def __init__(self, target, protocol, **kwargs):
        self.protocol               = protocol
        self.fgc                    = None
        self._timeout_s             = None
        self._token                 = None
        self._token_expiration_time = None
        self._target                = None
        self._protocol_object       = None

        self._process_args(target, kwargs)
        self._connect()

    def get(self, prop, get_option=None):
        if (    self._token_expiration_time
            and (self._token_expiration_time - int(time.time()) < 3600)):
            self._token = pyfgc_rbac.get_token_location()
            self._token_expiration_time = _get_token_expiration_time(self._token)
            self._protocol_object.renew_token(self._token)

        return self._protocol_object.get(prop, get_option=get_option)

    def set(self, prop, value):
        if (    self._token_expiration_time
            and (self._token_expiration_time - int(time.time()) < 3600)):
            self._token = pyfgc_rbac.get_token_location()
            self._token_expiration_time = _get_token_expiration_time(self._token)
            print(f'token renewed: new expiration time {self._token_expiration_time}')
            self._protocol_object.renew_token(self._token)
            
        return self._protocol_object.set(prop, value)

    def _connect(self):
        try:
            self._protocol_object.connect({self._target}, self._token, self._timeout_s)

        except AttributeError as e:
            raise AttributeError(f"Protocol object {self.protocol} has no connect function") from e

    def disconnect(self):
        self._protocol_object.disconnect()

    def _process_args(self, target, kwargs):
        self._target                = target if self.protocol == "serial" else _resolve_from_name_file(target, kwargs.get("name_file"))
        self._timeout_s             = kwargs.get("timeout_s", DEFAULT_TIMEOUT_S)
        
        self._protocol_object = _get_protocol_module(self.protocol)
        if self.protocol == "serial":
            self._token = None

        else:
            try:
                self._token = kwargs["rbac_token"]
                if self._token is None:
                    self._token = _acquire_token()

            except KeyError:
                self._token = _acquire_token()
                
        self._token_expiration_time  = _get_token_expiration_time(self._token)
        self.fgc                     = self._target



class FgcAsyncSession:
    def __init__(self, target, protocol, loop, instance_called=False, **kwargs):
        if not instance_called:
            raise NotImplementedError("FgcAsyncSession must not be called directly. "
                                      "Use FgcAsynSession.instance() instead.")

        self.fgc              = target
        self.protocol         = protocol
        self._timeout_s       = None
        self._token           = None
        self._target          = None
        self._protocol_object = None
        self.loop             = loop

    @staticmethod
    async def instance(target, protocol, loop=None, **kwargs):
        current_loop = loop if loop else asyncio.get_event_loop()
        obj = FgcAsyncSession(target, protocol, current_loop, instance_called=True)
        await obj._process_args(target, kwargs)
        await obj._connect()
        return obj

    async def get(self, prop, get_option=None):
        return await self._protocol_object.get(prop, get_option=get_option)

    async def set(self, prop, value):
        return await self._protocol_object.set(prop, value)

    async def _connect(self):
        try:
            await self._protocol_object.connect(self.loop, {self._target}, self._token, self._timeout_s)

        except AttributeError as e:
            raise AttributeError(f"Protocol object {self.protocol} has no connect function") from e

    async def disconnect(self):
        await self._protocol_object.disconnect()

    def _process_args_sync(self, target, kwargs):
        self._target          = _resolve_from_name_file(target, kwargs.get("name_file"))
        self._protocol_object = _get_protocol_module(self.protocol)
        self._timeout_s = kwargs.get("timeout_s", DEFAULT_TIMEOUT_S)
        
        try:
            self._token = kwargs["rbac_token"]
            if self._token is None:
                self._token = _acquire_token()
            
        except KeyError:
            self._token = _acquire_token()

    async def _process_args(self, target, kwargs):
        with concurrent.futures.ThreadPoolExecutor() as pool:
            await self.loop.run_in_executor(pool, self._process_args_sync, target, kwargs)


def _resolve_from_name_file(target, namefile=None):
    try:
        pyfgc_name.read_name_file(namefile)

    except FileNotFoundError as e:
        if namefile is None:
            raise FileNotFoundError("Unable to find default name file") from e
        else:
            raise FileNotFoundError(f"Unable to find name file {namefile}") from e

    resolved_targets = pyfgc_name.build_device_tset(target)

    if len(resolved_targets) == 0:
        raise KeyError(f"Did not find device named like {target}")

    if len(resolved_targets) > 1:
        raise KeyError(f"Target {target} matches more than one device")

    return resolved_targets.pop()


def _get_protocol_module(protocol):
    proto_string = "pyfgc.protocols." + protocol + "_fgc"

    try:
        protocol_module = importlib.import_module(proto_string)

    except TypeError as te:
        raise TypeError(f"Error getting protocol module: {te}") from te

    except ModuleNotFoundError as me:
        raise ModuleNotFoundError(f"{me}")

    else:
        protocol_object_name = protocol.capitalize() + "Fgc"
        return getattr(protocol_module, protocol_object_name)()

def _acquire_token():
    try:
        return pyfgc_rbac.get_token_location()

    except pyfgc_rbac.RbacServerError:
        return None

def _get_token_expiration_time(token):
    if not token:
        return None
    
    try:
        return int(pyfgc_rbac.token_to_dict(token)['ExpirationTime'])

    except TypeError:
        return None

# EOF
