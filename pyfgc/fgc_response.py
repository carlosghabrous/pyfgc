import re

NET_RSP_VOID        = b""
NET_RSP_BIN_FLAG    = b"\xFF"
NET_RSP_END         = b";"

SCRP_SUCCESS        = re.compile(rb"\$(?!\xff)([\w\W]*)\n;")
SCRP_SUCCESS_BIN    = re.compile(rb"\$\xff([\x00-\xff]*)\n;$")
SCRP_ERROR          = re.compile(rb"\$[\w\W]*\$([\w\W]*)\n!")

NCRP_SUCCESS        = re.compile(rb"\$(\d{0,31})\s{1}\.\n(?!\xff)([\w\W]*)\n;")
NCRP_SUCCESS_BIN    = re.compile(rb"\$(\d{0,31})\s{1}\.\n\xff([\x00-\xff]*)\n;$")
NCRP_ERROR          = re.compile(rb"\$(\d{0,31})\s{1}!\n([\w\W]*)\n;")

ERROR_CODE_MESSAGE  = re.compile(r"\s*(\d{1,})([\w\W]*)")

class FgcResponseError(Exception):
    pass

class FgcSingleResponse:
    """Single response from an FGC.
    
    Raises:
        TypeError: Raised when the response argument passed to build the object is not a byte string.
        FgcResponseError: Raised when an attemp to get the value is made but the object symbolizes an error. 
    
    Returns:
        FgcSingleResponse -- FgcSingleResponse object. 
    """
    def __init__(self, protocol, response=b"", err_policy="ignore"):
        self._value    = ""
        self._err_code = ""
        self._err_msg  = ""
        self._tag      = ""
        self.protocol  = protocol

        if not isinstance(response, bytes):
            raise TypeError(f"FgcSingleResponse can only be built from a byte string: {response}")
        
        self._value, self._err_code, self._err_msg, self._tag = getattr(self, FgcSingleResponse.rsp_parsers[protocol])(response, err_policy)
    
    @staticmethod
    def parser_serial(rsp, err_policy):
        """Parses serial responses. 
        
        Arguments:
            rsp {bytes} -- Byte string received from the FGC.
            err_policy {string} -- Policy for decoding errors (defaults to ignore)
        
        Returns:
            tuple -- value, err_code, err_msg, tag
        """
        value, err_code, err_msg, tag = "", "", "", ""
        m = SCRP_SUCCESS.search(rsp)
        if m:
            value = m.group(1).decode(errors=err_policy)

        m = SCRP_SUCCESS_BIN.search(rsp)
        if m:
            value = m.group(1).decode(errors=err_policy)

        m = SCRP_ERROR.search(rsp)
        if m:
            error_string = m.group(1).decode(errors=err_policy)
            err_code = ERROR_CODE_MESSAGE.search(error_string).group(1)
            err_msg  = ERROR_CODE_MESSAGE.search(error_string).group(2)

        return value, err_code, err_msg, tag

    @staticmethod
    def parser_net(rsp, err_policy):
        """Parses network responses, for both the sync and async protocols.
        
        Arguments:
            rsp {bytes} -- Byte string received from the FGC.
            err_policy {string} -- Policy for decoding errors (defaults to ignore)
        
        Returns:
            tuple -- value, err_code, err_msg, tag
        """
        value, err_code, err_msg, tag = "", "", "", ""
        m = NCRP_SUCCESS.search(rsp)
        if m:
            tag, value = m.group(1).decode(errors=err_policy), m.group(2).decode(errors=err_policy)

        m = NCRP_SUCCESS_BIN.search(rsp)
        if m:
            tag, value = m.group(1).decode(errors=err_policy), m.group(2)

        m = NCRP_ERROR.search(rsp)
        if m:
            tag, error_string = m.group(1).decode(errors=err_policy), m.group(2).decode(errors=err_policy)
            err_code = ERROR_CODE_MESSAGE.search(error_string).group(1)
            err_msg  = ERROR_CODE_MESSAGE.search(error_string).group(2)

        return value, err_code, err_msg, tag


    rsp_parsers = {"serial" : "parser_serial",
                    "sync"  : "parser_net",
                    "async" : "parser_net"}
    
    
    @property
    def tag(self):
        return self._tag

    @property 
    def value(self):
        if (not self._value
            and (self._err_code or self._err_msg)):
            raise FgcResponseError(f"{self._err_code}:{self._err_msg}")
            
        return self._value
    
    @property
    def err_code(self):
        return self._err_code
    
    @property
    def err_msg(self):
        return self._err_msg
        
    def __str__(self):
        return f"<FgcSingleResponse: 'tag={self._tag}' 'value={self._value}' 'err_code={self._err_code}' 'err_msg={self._err_msg}'>"


class FgcResponse:
    """Response from multiple FGCs.

    An object of this class behaves essentially as a dictionary of [string] - [FgcSingleResponse].
    
    Raises:
        TypeError: Raised if an item of type different than FgcSingleResponse is assigned to this object.
        FgcResponseError: [description]
    
    Returns:
        FgcResponse -- Groups responses from multiple FGCs.
    """
    fgc_protocols = ["serial", "sync", "async"]

    def __init__(self, protocol, raw_rsp=dict()):
        if protocol.lower() not in self.fgc_protocols:
            raise FgcResponseError(f"FgcResponse: unrecognized FGC protocol {protocol}")

        self.protocol = protocol
        self._fgc_rsp = dict()

        for k, v in raw_rsp.items():
            if not k.strip():
                self._fgc_rsp.clear()
                raise FgcResponseError(f"Attempt to build FgcResponse with empty device")

            self._fgc_rsp[k] = FgcSingleResponse(protocol, v)

    @property
    def value(self):
        if len(self._fgc_rsp) == 0:
            return "" 

        if len(self._fgc_rsp) == 1:
            device = list(self._fgc_rsp.keys())[0]
            return self._fgc_rsp[device].value
        
        raise FgcResponseError("Multiple device FgcResponse: 'value' is accesible by keys only")

    @property
    def tag(self):
        if len(self._fgc_rsp) == 0:
            return "" 

        if len(self._fgc_rsp) == 1:
            device = list(self._fgc_rsp.keys())[0]
            return self._fgc_rsp[device].tag

        raise FgcResponseError("Multiple device FgcResponse: 'tag' is accesible by keys only")

    @property
    def err_msg(self):
        if len(self._fgc_rsp) == 0:
            return "" 

        if len(self._fgc_rsp) == 1:
            device = list(self._fgc_rsp.keys())[0]
            return self._fgc_rsp[device].err_msg

        raise FgcResponseError("Multiple device FgcResponse: 'err_msg' is accesible by keys only")

    @property
    def err_code(self):
        if len(self._fgc_rsp) == 0:
            return "" 

        if len(self._fgc_rsp) == 1:
            device = list(self._fgc_rsp.keys())[0]
            return self._fgc_rsp[device].err_code

        raise FgcResponseError("Multiple device FgcResponse: 'err_code' is accesible by keys only")

    # Magic methods
    def __len__(self):
        return len(self._fgc_rsp)

    def __contains__(self, item):
        return item in self._fgc_rsp.keys()

    def __iter__(self):
        for k in self._fgc_rsp.keys():
            yield k
    
    def __getitem__(self, device):
        return self._fgc_rsp[device]

    def __setitem__(self, device, rsp):
        if not isinstance(rsp, FgcSingleResponse):
            raise TypeError("FgcResponse items must be FgcSingleResponse objects")

        if self.protocol != rsp.protocol:
            raise FgcResponseError(f"FgcSingleResponse protocol {rsp.protocol} != FgcResponse protocol {self.protocol}")
        
        self._fgc_rsp[device] = rsp

    def __str__(self):
        indv_rsps = list()
        for k in self._fgc_rsp:
            indv_rsps.append(str(self._fgc_rsp[k]))

        new_line = "\n"
        return f"<FgcResponse: '{self.protocol}' '{new_line.join(indv_rsps)}'>"

