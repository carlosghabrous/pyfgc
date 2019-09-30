import importlib

import pyfgc_name
import pyfgc_rbac
from .fgc_response import FgcResponse

#TODO: Remove the double start from kwargs (I don't think right now that 
# FgcSession objects will be created directly without passing through the API
# module).

DEFAULT_TIMEOUT_S = 1

class FgcSession:
    def __init__(self, targets, protocol, **kwargs):
        self.protocol = protocol
        self._token = None
        self.timeout_s = None

        self._target_set = None
        self._proto_module = None

        self._process_args(targets, kwargs)

        try:
            self._proto_module.connect(self._target_set, self._token, self.timeout_s)

        except AttributeError:
            raise AttributeError(f"Protocol module {self.protocol} has no connect function")
        #TODO: what happens with other exceptions? Just let the client handle them?


    def add_connection(self, targets):
        new_target_set = pyfgc_name.build_device_set(targets)
        self._proto_module.connect(new_target_set, self.protocol, self.timeout_s)
        self._target_set |= new_target_set

    def get(self, prop, get_option=None, targets=None):
        return self._proto_module.get(prop, get_option=get_option, targets=pyfgc_name.build_device_set(targets))

    def set(self, prop, value):
        return self._proto_module.set(prop, value)
    
    def disconnect(self, targets=None):
        # Disconnect only 'targets' or all of existing connections
        dis_targets = pyfgc_name.build_device_set(targets) or self._target_set
        try:     
            self._proto_module.disconnect(targets=dis_targets)
        
        #TODO: which type of exception
        except Exception:
            pass
        
        self._target_set -= dis_targets        

    def _process_args(self, targets, kwargs):
        self._set_protocol_module(self.protocol)
        
        # Get timeout. TODO: necessary?
        self.timeout_s = kwargs.get("timeout_s", DEFAULT_TIMEOUT_S)

        if self.protocol == "serial":
            self._target_set = set([targets]) 
            return

        # Get name file from argument or default
        try:
            name_file = kwargs["name_file"]

        except KeyError:
            pyfgc_name.read_name_file()

        else:
            pyfgc_name.read_name_file(name_file)

        # Build target list from targets
        self._target_set = pyfgc_name.build_device_set(targets)

        #TODO: might be better to return an empty response instead of rising an exception?
        # How to communicate that to the client though?
        if not self._target_set:
            raise RuntimeError(f"Did not find targets named like {targets}, or targets were empty")

        # TODO: who does the token acquisition? Could make more sense to do it
        # from the connection pool, as a serial connection won't needed, for instance, and at the
        # same time it will have a session object underneath
        # Get RBAC token from argument or try get by location. If location fails, it is set to None
        try:
            self._token = kwargs["rbac_token"]

        except KeyError:
            self._acquire_token()


    def _acquire_token(self):
        try:
            self._token = pyfgc_rbac.get_token_location()

        #TODO: what kind of exception?
        except Exception:
            self._token = None
        
    def _set_protocol_module(self, protocol):
        try:
            proto_string = "pyfgc.protocols." + protocol + "_fgc"
            self._proto_module = importlib.import_module(proto_string)

        except TypeError as te:
            raise TypeError(f"Error getting protocol module: {te}")

        except ModuleNotFoundError as me:
            raise ModuleNotFoundError(f"{me}")

    def __len__(self):
        return len(self._target_set)
            
