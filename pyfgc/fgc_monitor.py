# import asyncio
# import os
# import collections
import math
import re
import heapq
import itertools
import logging
import sys
import socket
import select
import threading
import struct
import time
import inspect
from pyfgc_decoders import decode
import pyfgc_name
import pyfgc_rbac

logger = logging.getLogger('pyfgc.fgc_monitor')
logger.setLevel(logging.INFO)

GW_PORT = 1905
TCP_SETUP_TIMEOUT = 1.0
THREAD_JOIN_TIMEOUT = 1.0
RETRY_CONNECTION_MARGIN = 1.0
RETRY_CONNECTION_PERIOD = 10.0
FGC_CYCLE_TIME = 0.02

class SingletonMeta(type):
    '''
    Used for singleton creation.
    '''
    object_instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls.object_instances:
            cls.object_instances[cls] = super(SingletonMeta,cls).__call__(*args, **kwargs)
        return cls.object_instances[cls]


class CallbackHandler:
    '''
    Handles a client subscription to a shared session.
    '''

    def __init__(self):
        self.callback = None
        self.callback_err = None
        self.timeout = None
        self.timeout_abs = None
        self.session = None

    def reset_timeout(self, timestamp=None):
        if self.timeout:
            curr_time = timestamp if timestamp else time.time()
            self.timeout_abs = curr_time + self.timeout


class SessionData:
    '''
    Session (with TCP subscription) data.
    '''

    def __init__(self, address, sub_id, sub_period, token):
        self.active = False
        self.clients = 0
        self.tcp_socket = None
        self.udp_socket = None
        self.udp_port = None
        self.sub_id = sub_id
        self.sub_period = sub_period
        self.sub_token = token
        self.sub_address = address
        self.handlers = set()
        self.reconnect_time = None

    def clean(self):
        self.active = False
        try:
            self.tcp_socket.close()
            self.udp_socket.close()
        except AttributeError:
            pass
        logger.info("Stopped monitoring {}.".format(str(self)))

    def start(self):
        self.udp_socket = new_udp_socket(0)
        self.udp_port = self.udp_socket.getsockname()[1]
        self.tcp_socket = new_tcp_session(self.sub_address, self.udp_port, self.sub_period, self.sub_id, self.sub_token)
        self.active = True
        self.reset_timeout()
        logger.info("Started monitoring {}.".format(str(self)))

    def reset_timeout(self, timestamp=None):
        curr_time = timestamp if timestamp else time.time()
        self.reconnect_time = curr_time + RETRY_CONNECTION_MARGIN + (self.sub_period / 50)

    def __str__(self):
        has_token_str = "Yes" if self.sub_token else "No"
        return "[Machine: {}; Period: {}; Token: {}]".format(self.sub_address, self.sub_period, has_token_str)

class SessionlessData:
    '''
    Sessionless (no TCP subscription) data.
    '''

    def __init__(self, udp_port):
        self.active = False
        self.clients = 0
        self.udp_socket = None
        self.udp_port = udp_port
        self.handlers = set()
        self.reconnect_time = None # No period, no timeout

    def clean(self):
        self.active = False
        try:
            self.udp_socket.close()
        except AttributeError:
            pass
        logger.info("Stopped monitoring {}.".format(str(self)))

    def start(self):
        self.udp_socket = new_udp_socket(self.udp_port)
        self.active = True
        logger.info("Started monitoring {}.".format(str(self)))

    def reset_timeout(self, timestamp=None):
        pass # Implementation ignored

    def __str__(self):
        return "[Port: {}]".format(self.udp_port)

class MonitorLoop(metaclass=SingletonMeta):
    '''
    Used for handling multiple (shared) sessions and subscriptions
    '''

    def __init__(self):

        logger.info("Starting MonitorLoop...")

        # Managed sessions

        self.session_data = dict()
        self.sessions_on_try = dict()

        # Setup thread

        self.ksock_r, self.ksock_s = socket.socketpair()
        self.thread = threading.Thread(target=self._listening_thread_wrap)
        self.thread.daemon = True
        self.thread_alive = True
        self.thread_exception = None
        self.thread.start()
        self.rlock = threading.RLock()

    def _add_new_handler(self, session, callback, callback_err, timeout):

        def callback_err_safe(err, curr_time):
            try:
                callback_err(err, curr_time)
            except Exception:
                logger.exception("Callback err failed.")

        def callback_safe(data_dict, data_list, curr_time):
            try:
                callback(data_dict, data_list, curr_time)
            except Exception as err:
                logger.exception("Callback failed.")
                callback_err_safe(err, curr_time)

        handler = CallbackHandler()
        handler.callback = callback_safe
        handler.callback_err = callback_err_safe
        handler.timeout = timeout
        handler.session = session
        handler.reset_timeout()

        with self.rlock:
            new_handler_set = set(session.handlers)
            new_handler_set.add(handler)
            session.clients += 1
            session.handlers = new_handler_set

        return handler

    def _remove_handler(self, handler):

        session = handler.session
        with self.rlock:
            new_handler_set = set(session.handlers)
            new_handler_set.remove(handler)
            session.handlers = new_handler_set
            session.clients -= 1

        return session

    def subscribe_session(self, callback, callback_err, ip_address, sub_period, token=None, timeout=None):

        sub_address = ip_address.lower()

        with self.rlock:
            try:
                session = self.session_data[sub_address, sub_period, token]
            except KeyError:
                session = SessionData(sub_address, 0, sub_period, token)
                self.session_data[sub_address, sub_period, token] = session
                self._try_session_delay(session, delay=0)
            handler = self._add_new_handler(session, callback, callback_err, timeout)

        self.ksock_s.send(b"\xff")
        logger.info("New subscription to session {}.".format(str(session)))
        return handler

    def subscribe_port(self, callback, callback_err, udp_port, timeout=None):

        with self.rlock:
            try:
                session = self.session_data[udp_port]
            except KeyError:
                session = SessionlessData(udp_port)
                self.session_data[udp_port] = session
                self._try_session_delay(session, delay=0)
            handler = self._add_new_handler(session, callback, callback_err, timeout)

        self.ksock_s.send(b"\xff")
        logger.info("New subscription to session {}.".format(str(session)))
        return handler

    def unsubscribe_session(self, handler):

        with self.rlock:
            session = self._remove_handler(handler)
            if session.clients <= 0:
                del self.session_data[session.sub_address, session.sub_period, session.sub_token]
                session.clean()

        self.ksock_s.send(b"\xff")
        logger.info("Removed subscription to session {}.".format(str(session)))

    def unsubscribe_port(self, handler):

        with self.rlock:
            session = self._remove_handler(handler)
            if session.clients <= 0:
                del self.session_data[session.udp_port]
                session.clean()

        self.ksock_s.send(b"\xff")
        logger.info("Removed subscription to session {}.".format(str(session)))

    def _try_session_delay(self, s, delay=None):

        delay = RETRY_CONNECTION_PERIOD if delay is None else delay

        def _try():

            curr_time = time.time()

            try:
                s.start()
            except ConnectionRefusedError:
                logger.error("Failed activation of session {}. Connection refused.".format(str(s)))
            except Exception as err:
                logger.exception("Failed activation of session {}. Unexpected error.".format(str(s)))
                for handler in s.handlers:
                    handler.callback_err(err, curr_time)
            else:
                logger.info("Session {} activated successfully.".format(str(s)))
                s.reset_timeout()
            finally:
                if s in self.sessions_on_try:
                    del self.sessions_on_try[s]
                self.ksock_s.send(b"\xff")

        if s not in self.sessions_on_try:
            t = threading.Timer(delay, _try)
            self.sessions_on_try[s] = t
            t.start()
            logger.info("Ordered activation of session {} in {} seconds.".format(str(s), delay))

    def _listening_thread_wrap(self):

        try:
            self._listening_thread_func()
        except Exception as exc:
            logger.exception("Monitor thread failed abruptly.")
            self.thread_exception = exc
            #curr_time = time.time()
            #for session in self.session_data.values():
            #    for handler in session.handlers:
            #        handler.callback_err(exc, curr_time)
            # If thread fails, something is really wrong. Should raise.
            raise
        else:
            self.thread_exception = None
        finally:
            self.thread_alive = False

    def _listening_thread_func(self):

        logger.info("MonitorLoop thread running.")

        while self.thread_alive:

            # Order reactivation of inactive sessions

            for s in self.session_data.values():
                if not s.active:
                    self._try_session_delay(s)

            # Check active sessions

            udp_sock_sessions = {s.udp_socket : s for s in self.session_data.values() if s.active}

            # Grouping sockets

            sockets = set()
            sockets.add(self.ksock_r)
            sockets.update(udp_sock_sessions.keys())

            # Check handler timeouts

            counter = itertools.count() # Tie breaker for priority queues

            handlers = set()
            for session in self.session_data.values(): # Include all, including inactive sessions
                for handler in session.handlers:
                    handlers.add(handler)

            timeout_handlers = [(handler.timeout_abs, next(counter), handler) for handler in handlers if handler.timeout]
            heapq.heapify(timeout_handlers)

            # Check TCP session timeouts

            sessions = udp_sock_sessions.values()
            timeout_sessions = [(session.reconnect_time, next(counter), session) for session in sessions if session.reconnect_time]
            heapq.heapify(timeout_sessions)

            # Check next timeout

            if not timeout_handlers and not timeout_sessions:
                timeout = None
            else:
                timeout_arr = []
                timeout_arr += [timeout_handlers[0][0]] if timeout_handlers else []
                timeout_arr += [timeout_sessions[0][0]] if timeout_sessions else []
                timeout_abs = min(timeout_arr)
                timeout = timeout_abs - time.time()
                timeout = timeout if timeout > 0 else 0
                # Round up any timeout to the near 5 FGC cycles, 0.1 seconds (or any other value).
                # This is important to to avoid timeout spamming, caused by multiple handlers timeouts
                # being triggered at different times.
                logger.debug(f"{timeout_arr}")
                timeout = roundup(timeout, 5*FGC_CYCLE_TIME)

            # Wait for next incoming data, or for a timeout

            logger.debug(f"Waiting on sockets with a timeout of {timeout} s.")
            recv_socks,_,_ = select.select(sockets, {}, {}, timeout)
            curr_time = time.time()

            # Timeout for callback handlers

            timedout_handlers = set()

            try:
                while True:
                    timeout_abs, _, handler = heapq.heappop(timeout_handlers)
                    if timeout_abs > curr_time:
                        break
                    timedout_handlers.add(handler)
            except IndexError:
                pass

            for session in {handler.session for handler in timedout_handlers}:
                logger.warning("Handler timeout detected on session {}.".format(str(session)))

            for handler in timedout_handlers:
                handler.callback(None, None, curr_time)
                handler.reset_timeout(timestamp=curr_time)

            # Timeout for sessions

            try:
                while True:
                    timeout_abs, _, session = heapq.heappop(timeout_sessions)
                    logger.warning("Timeout detected on session {}.".format(str(session)))
                    if timeout_abs > curr_time:
                        break
                    err = RuntimeError("Session timeout, disabling session...")
                    for handler in session.handlers:
                        handler.callback_err(err, curr_time)
                    session.clean()
                    session.reset_timeout(timestamp=curr_time)
            except IndexError:
                pass

            # Sockets

            for s in recv_socks:

                # Resolve session

                if s is self.ksock_r:
                    self.ksock_r.recv(1)
                    logger.debug("Wakeup signal received by thread.")

                else:
                    session = udp_sock_sessions[s]

                    if not session.active:
                        logger.warning("Received data on inactive session {}. Ignoring data.".format(str(session)))
                        session.clean()
                        continue

                    try:
                        data, addr = session.udp_socket.recvfrom(4096)
                    except OSError as e:
                        logger.exception("UDP socket failed. Disconnecting.")
                        session.clean()
                        try:
                            raise OSError("Connection failed (failed to read UDP socket). Disconnected.") from e
                        except Exception as new_exc:
                            err = new_exc

                        for handler in session.handlers:
                            handler.callback_err(err, curr_time)
                    else:
                        logger.debug("Received data on session {}".format(str(session)))
                        session.reset_timeout(curr_time)

                        for handler in session.handlers:
                            handler.callback(data, addr, curr_time)
                            handler.reset_timeout()

        logger.info("Closing MonitorLoop thread.")

        for s, t in self.sessions_on_try.items():
            logger.info("Cancelling reactivation of session {}.".format(str(s)))
            t.cancel()
        self.sessions_on_try.clear()

        for session in self.session_data.values():
            session.clean()
        self.session_data.clear()

def roundup(value, base):
    return base * math.ceil(value/base)

def new_udp_socket(udp_port):
    '''
    Opens a new UDP endpoint for receiving subscrition data. If port is 0, a
    random free port will be used.
    Returns the new UDP socket.
    If this port already exists, it is returned instead
    '''
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', udp_port))

    logger.info("New UDP port opened ({}).".format(s.getsockname()[1]))
    return s

def new_tcp_session(address, sub_port, sub_period, sub_id=0, sub_token=None):
    '''
    Opens a new TCP connection to a gateway, and setup a status publication
    subscription.
    Returns the new TCP socket.
    '''

    CMD_TOKEN_HALF = f"! S:CLIENT.TOKEN "
    CMD_ID = f"! S :CLIENT.UDP.SUB.ID {sub_id}\n"
    CMD_PERIOD = f"! S :CLIENT.UDP.SUB.PERIOD {sub_period}\n"
    CMD_PORT = f"! S :CLIENT.UDP.SUB.PORT {sub_port}\n"
    OK_REGEX = re.compile(rb"\$ \.\n\n;")

    # Create TCP session socket

    try:
        s = socket.socket()
        s.settimeout(TCP_SETUP_TIMEOUT)
        s.connect((address, GW_PORT))
    except Exception as e:
        logger.exception(f"Could not open socket with gateway {address}.")
        raise

    # Hanshake

    if s.recv(1) != b"+":
        s.close()
        err_msg = f"Handshake with gateway {address} not successful."
        logger.error(err_msg)
        raise ConnectionError(err_msg)
    else:
        s.sendall(b"+")

    # Set subscription properties and token

    def send_cmd(cmd, s):
        s.sendall(cmd)
        resp = bytearray()

        while b';' not in resp:
            resp += s.recv(1024)

        if not re.match(OK_REGEX, resp):
            err_msg = f"{cmd} failed with {resp.decode()}"
            logger.error(err_msg)
            raise ConnectionError(err_msg)

    try:
        if sub_token:
            cmd = CMD_TOKEN_HALF.encode() + struct.pack('!BL', 255, len(sub_token)) + sub_token + "\n".encode()
            send_cmd(cmd, s)
        send_cmd(CMD_ID.encode(), s)
        send_cmd(CMD_PERIOD.encode(), s)
        send_cmd(CMD_PORT.encode(), s)
    except ConnectionError as e:
        s.close()
        raise

    # Remove timeout

    s.settimeout(0)
    logger.info(f"New TCP connection opened ({address}).")
    return s

# Hostname to IP conversion, with caching

try:
    hostname_to_ip
except NameError:
    hostname_to_ip = dict()

def resolve_hostnames(addr_set):

    addr_to_ip = dict()

    for addr in addr_set:
        try:
            ip_addr = hostname_to_ip[addr]
        except KeyError:
            try:
                ip_addr = socket.gethostbyname(addr)
            except OSError:
                continue
        addr_to_ip[addr] = ip_addr

    hostname_to_ip.update(addr_to_ip)
    return addr_to_ip

# IP to hostname conversion, with caching

try:
    ip_to_hostname
except NameError:
    ip_to_hostname = dict()

def resolve_ips(ip_set):

    ip_to_addr = dict()

    for ipa in ip_set:
        try:
            host = ip_to_hostname[ipa]
        except KeyError:
            try:
                hostname = socket.gethostbyaddr(ipa)[0]
                host = hostname.split('.')[0]
            except OSError:
                continue
        ip_to_addr[ipa] = host

    ip_to_hostname.update(ip_to_addr)
    return ip_to_addr

# Decode data, with caching

try:
    decoded_data_cache
except NameError:
    decoded_data_cache = dict()

def decode_data(gateway, timestamp, raw_data):
    '''
    Will cache decoded values. Valid for only same timestamp.
    '''

    try:
        decoded_data, prev_timestamp = decoded_data_cache[gateway]
    except KeyError:
        pass
    else:
        if timestamp == prev_timestamp:
            return decoded_data

    data_dict = {}
    data_list = decode(raw_data)

    devices = pyfgc_name.gateways[gateway.lower()]["devices"]

    for device_name in devices:
        device_channel = pyfgc_name.devices[device_name.upper()]["channel"]
        data_list[device_channel]["CHANNEL"] = device_channel
        data_list[device_channel]["NAME"] = device_name.upper()
        data_dict[device_name.upper()] = data_list[device_channel]

    result = (data_dict, data_list)
    decoded_data_cache[gateway] = (result, timestamp)
    return result

def refresh_name_file(name_file=None):
    if name_file:
        try:
            pyfgc_name.read_name_file(name_file)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Unable to find name file {name_file}.") from e
    else:
        try:
            pyfgc_name.read_name_file()
        except FileNotFoundError as e:
            raise FileNotFoundError("Unable to find default name file.") from e


# Token acquisition

def acquire_token():
    try:
        return pyfgc_rbac.get_token_location()
    except pyfgc_rbac.RbacServerError:
        return None

def validate_callback(func):
    arg_signature = inspect.signature(func)
    arg_parameters = list(arg_signature.parameters.values())
    if len(arg_parameters) == 4 or \
        (len(arg_parameters) != 0 and \
         arg_parameters[0].kind == arg_parameters[0].VAR_POSITIONAL):
        pass
    else:
        raise TypeError("FGC monitor callback must contain 4 positional arguments: "
                        "(data_dict, data_list, gateway, timestamp).")

def validate_callback_err(func):
    arg_signature = inspect.signature(func)
    arg_parameters = list(arg_signature.parameters.values())
    if len(arg_parameters) == 3 or \
        (len(arg_parameters) != 0 and \
         arg_parameters[0].kind == arg_parameters[0].VAR_POSITIONAL):
        pass
    else:
        raise TypeError("FGC monitor error callback must contain 3 positional arguments: "
                        "(error, gateway, timestamp).")

class MonitorSession:

    def __init__(self, callback, targets, sub_period, timeout=None, callback_err=None, **kwargs):

        # Refresh name file
        name_file = kwargs.get('name_file', None)
        refresh_name_file(name_file)

        # Parse arguments
        gw_dev_tuples = pyfgc_name.build_device_tset(targets)

        self.targets = targets
        self.gateways = {gw for dev,gw in gw_dev_tuples}
        self.ips = resolve_hostnames(self.gateways)
        self.devices = {dev for dev,gw in gw_dev_tuples}
        self.sub_period = sub_period

        self.callback = callback
        self.callback_err = callback_err
        self.timeout = timeout

        # Validate callbacks
        validate_callback(self.callback)
        if self.callback_err:
            validate_callback_err(self.callback_err)

        # Acquire token
        try:
            self.token = kwargs["rbac_token"]
        except KeyError:
            self.token = acquire_token()

        # Get monitor
        self.monitor_loop = MonitorLoop()
        self.subscription_handlers = set()

    def _generate_callback(self, gateway):

        def _callback(data, addr, curr_time):

            # TODO: Validate address!

            if data and addr:
                data_dict, data_list = decode_data(gateway, curr_time, data)
                self.callback(data_dict, data_list, gateway, curr_time)
            else:
                self.callback(None, None, gateway, curr_time)

            logger.debug(f"Ran callback for gateway {gateway}.")

        return _callback

    def _generate_callback_err(self, gateway):

        def _callback_err(err, curr_time):
            self.callback_err(err, gateway, curr_time)
            logger.debug(f"Ran callback error for gateway {gateway}.")

        return _callback_err if  self.callback_err else None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args, **kwargs):
        self.stop()

    def start(self):

        for gw in self.gateways:

            if gw in self.ips:
                sub_handler = self.monitor_loop.subscribe_session(
                        self._generate_callback(gw),
                        self._generate_callback_err(gw),
                        self.ips[gw],
                        self.sub_period,
                        self.token,
                        self.timeout)
                self.subscription_handlers.add(sub_handler)
            else:
                pass
                # TODO: Log this event!!!

    def stop(self):

        for handler in self.subscription_handlers:
            self.monitor_loop.unsubscribe_session(handler)



class MonitorPort:

    def __init__(self, callback, sub_port, filter_id=None, filter_address=None, timeout=None, callback_err=None, **kwargs):

        # Refresh name file
        name_file = kwargs.get('name_file', None)
        refresh_name_file(name_file)

        # Parse arguments
        self.sub_port = sub_port
        self.callback = callback
        self.callback_err = callback_err
        self.timeout = timeout

        # Validate callbacks
        validate_callback(self.callback)
        if self.callback_err:
            validate_callback_err(self.callback_err)

        # Filtering
        self.filter_id = {filter_id} if isinstance(filter_id, int) else (set(filter_id) if isinstance(filter_id, (list, set)) else None)
        filter_addr = {filter_address} if isinstance(filter_address, str) else (set(filter_address) if isinstance(filter_address, (list, set)) else None)
        self.filter_ip = set(resolve_hostnames(filter_addr).values()) if filter_addr else None

        if not self.filter_id and filter_id:
            raise TypeError("Wrong type parameter: filter_id")
        if not self.filter_ip and filter_address:
            raise TypeError("Wrong type parameter: filter_address")

        # Get monitor
        self.monitor_loop = MonitorLoop()
        self.sub_handler = None
        self.ip_to_host = dict()

    def _generate_callback(self):

        def _callback(data, addr, curr_time):

            if data and addr:

                # TODO: Filter by ID and IP address

                data_ip = addr[0]
                data_id, = struct.unpack(">I", data[:4])

                logger.debug(f"Port {self.sub_port} received packet from {data_ip}, with ID 0x{data_id:08X}.")
                logger.debug(self.filter_ip)
                if self.filter_ip and data_ip not in self.filter_ip:
                    return
                if self.filter_id and data_id not in self.filter_id:
                    return

                if data_ip not in self.ip_to_host:
                    self.ip_to_host.update(resolve_ips({data_ip}))

                try:
                    gateway = self.ip_to_host[data_ip]
                except KeyError:
                    # If not resolved, just call it by its IP address
                    gateway = data_ip

                data_dict, data_list = decode_data(gateway, curr_time, data)
                self.callback(data_dict, data_list, gateway, curr_time)
            else:
                self.callback(None, None, None, curr_time)

            logger.debug(f"Ran callback for port {self.sub_port}.")

        return _callback

    def _generate_callback_err(self):

        def _callback_err(err, curr_time):
            self.callback_err(err, None, curr_time)
            logger.debug(f"Ran callback error for port {self.sub_port}.")

        return _callback_err if self.callback_err else None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args, **kwargs):
        self.stop()

    def start(self):

        self.sub_handler = self.monitor_loop.subscribe_port(
                self._generate_callback(),
                self._generate_callback_err(),
                self.sub_port,
                self.timeout)

    def stop(self):

        self.monitor_loop.unsubscribe_port(self.sub_handler)

# EOF
