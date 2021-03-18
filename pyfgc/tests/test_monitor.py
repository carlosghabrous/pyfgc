# import time
# import threading
# from concurrent import futures
# import asyncio
# import pytest
# import pyfgc
# import socket
# import functools
# from contextlib import contextmanager
# import logging
# from pyfgc import fgc_monitor
# import pyfgc_rbac
# import pyfgc_decoders
# import pyfgc_name
# from importlib import reload # Required for reseting monitor loop singleton

# logger = logging.getLogger('pyfgc.fgc_monitor')
# logger.setLevel(logging.DEBUG)

# DEVICE_A1 = "RFNA.866.06.ETH1"
# DEVICE_A2 = "RFNA.866.07.ETH1"
# DEVICE_B1 = "RFNA.866.02.ETH2"
# GATEWAY_A = "CFC-866-RETH1"
# GATEWAY_B = "CFC-866-RETH2"
# GATEWAY_ERR = "DOES-NOT-EXIST"

# PORT_1 = 12345
# PORT_2 = 12346

# @pytest.fixture(scope="session", autouse=True)
# def get_rbac_token():

#     try:
#         token = pyfgc_rbac.get_token_location()
#     except pyfgc_rbac.RbacServerError:
#         token = None

#     def _foo():
#         return token

#     return _foo

# @pytest.fixture(scope="function")
# def reload_namefile():
#     pyfgc_name.read_name_file()

# @pytest.fixture(scope="function", autouse=True)
# def reload_fgc_monitor():
#     '''
#     fgc_monitor singleton must be restarted on every test!
#     '''
#     reload(fgc_monitor)
#     logger = logging.getLogger('pyfgc.fgc_monitor')
#     logger.setLevel(logging.DEBUG)

#     yield

#     monitor_loop = fgc_monitor.MonitorLoop()
#     monitor_loop.thread_alive = False

# @contextmanager
# def new_udp_stream(gateway, sub_period, sub_port, sub_id, token=None):
#     __tracebackhide__ = True
#     with pyfgc.fgc(gateway) as fgc_session:
#         if token:
#             res_0 = fgc_session.set("CLIENT.TOKEN", token)
#             res_0.value

#         res_1 = fgc_session.set("CLIENT.UDP.SUB.ID", sub_id)
#         res_2 = fgc_session.set("CLIENT.UDP.SUB.PERIOD", sub_period)
#         res_3 = fgc_session.set("CLIENT.UDP.SUB.PORT", sub_port)

#         # Will raise exception if any command failed

#         res_1.value
#         res_2.value
#         res_3.value

#         yield
#         return

# @contextmanager
# def session_subscription(monitor_loop, callback, callback_err, ip_address, sub_period, token=None, timeout=None):
#     __tracebackhide__ = True
#     handler = monitor_loop.subscribe_session(
#                 callback,
#                 callback_err,
#                 ip_address,
#                 sub_period,
#                 token,
#                 timeout
#             )
#     yield handler
#     monitor_loop.unsubscribe_session(handler)

# @contextmanager
# def port_subscription(monitor_loop, callback, callback_err, udp_port, timeout=None):
#     __tracebackhide__ = True
#     handler = monitor_loop.subscribe_port(
#                 sub_period,
#                 token,
#                 callback,
#                 callback_err,
#                 udp_port,
#                 timeout
#             )
#     yield handler
#     monitor_loop.unsubscribe_port(handler)

# def dummy_callback(**kwargs):
#     pass

# # Test MonitorLoop

# @pytest.fixture
# def start_monitorloop():
#     fgc_monitor.MonitorLoop()
#     time.sleep(.1)

# testdata_roundup = [
#     (0.0, 1.0, 0.0),
#     (0.1, 1.0, 1.0),
#     (1.0, 1.0, 1.0),
#     (-0.1, 1.0, 0.0),
#     (-1.0, 1.0, -1.0),
#     (0.0, 0.1, 0.0),
#     (0.1, 0.1, 0.1),
#     (1.0, 0.1, 1.0),
#     (-0.1, 0.1, -0.1),
#     (-1.0, 0.1, -1.0),
#     (0.0, 0.2, 0.0),
#     (0.1, 0.2, 0.2),
#     (1.0, 0.2, 1.0),
#     (-0.1, 0.2, 0.0),
#     (-1.0, 0.2, -1.0),
# ]

# @pytest.mark.parametrize("value_in,base,value_out", testdata_roundup)
# def test_roundup(value_in, base, value_out):
#     assert pytest.approx(fgc_monitor.roundup(value_in, base)) == value_out

# def test_monitorloop_running(start_monitorloop):
#     monitor_loop = fgc_monitor.MonitorLoop()
#     assert monitor_loop.thread_alive == True
#     assert monitor_loop.thread.is_alive()

# def test_monitorloop_singleton():
#     monitor_loop_1 = fgc_monitor.MonitorLoop()
#     monitor_loop_2 = fgc_monitor.MonitorLoop()
#     assert monitor_loop_1 is monitor_loop_2

# def test_new_udp_socket_1():
#     sock = fgc_monitor.new_udp_socket(0)
#     udp_port = sock.getsockname()[1]
#     assert udp_port and isinstance(udp_port, int)
#     sock.close()

# def test_new_udp_socket_2():
#     sock = fgc_monitor.new_udp_socket(12345)
#     udp_port = sock.getsockname()[1]
#     assert udp_port == 12345
#     sock.close()

# def test_new_udp_socket_reconnect():
#     sock = fgc_monitor.new_udp_socket(12345)
#     udp_port = sock.getsockname()[1]
#     assert udp_port == 12345
#     sock.close()
#     sock = fgc_monitor.new_udp_socket(12345)
#     udp_port = sock.getsockname()[1]
#     assert udp_port == 12345
#     sock.close()

# def test_new_tcp_session(get_rbac_token):
#     sock = fgc_monitor.new_tcp_session(GATEWAY_A, 12345, 10, sub_id=0, sub_token=get_rbac_token())
#     gateway_ip = socket.gethostbyname(GATEWAY_A)
#     sock_addr = sock.getpeername()[0]
#     sock_port = sock.getpeername()[1]
#     assert sock_addr == gateway_ip
#     assert sock_port == 1905
#     sock.close()

# def test_new_tcp_session_reconnect(get_rbac_token):
#     gateway_ip = socket.gethostbyname(GATEWAY_A)

#     sock = fgc_monitor.new_tcp_session(GATEWAY_A, 12345, 10, sub_id=0, sub_token=get_rbac_token())
#     sock_addr = sock.getpeername()[0]
#     sock_port = sock.getpeername()[1]
#     assert sock_addr == gateway_ip
#     assert sock_port == 1905
#     sock.close()

#     sock = fgc_monitor.new_tcp_session(GATEWAY_A, 12345, 10, sub_id=0, sub_token=get_rbac_token())
#     sock_addr = sock.getpeername()[0]
#     sock_port = sock.getpeername()[1]
#     assert sock_addr == gateway_ip
#     assert sock_port == 1905
#     sock.close()

# def test_session_data(get_rbac_token):
#     session = fgc_monitor.SessionData(GATEWAY_A, 0x0000, 50, get_rbac_token())
#     session.start()
#     assert session.active == True
#     assert session.tcp_socket.getsockname()
#     assert session.udp_socket.getsockname()
#     assert session.udp_port == session.udp_socket.getsockname()[1]
#     session.clean()
#     assert session.active == False
#     with pytest.raises(OSError):
#         assert session.tcp_socket.getsockname()
#     with pytest.raises(OSError):
#         assert session.udp_socket.getsockname()

# def test_session_data_restart(get_rbac_token):
#     session = fgc_monitor.SessionData(GATEWAY_A, 0x0000, 50, get_rbac_token())
#     session.start()
#     session.clean()
#     session.start()
#     assert session.active == True
#     assert session.tcp_socket.getsockname()
#     assert session.udp_socket.getsockname()
#     session.clean()

# def test_sessionless_data(get_rbac_token):
#     session = fgc_monitor.SessionlessData(12345)
#     session.start()
#     assert session.active == True
#     assert session.udp_socket.getsockname()
#     assert session.udp_port == 12345
#     session.clean()
#     assert session.active == False
#     with pytest.raises(OSError):
#         assert session.udp_socket.getsockname()

# def test_sessionless_data_restart(get_rbac_token):
#     session = fgc_monitor.SessionlessData(12345)
#     session.start()
#     session.clean()
#     session.start()
#     assert session.active == True
#     assert session.udp_socket.getsockname()
#     session.clean()

# def test_monitorloop_session_callback(get_rbac_token):

#     callback_fut = futures.Future()

#     def callback(*args, **kwargs):
#         callback_fut.set_result(True)

#     monitor_loop = fgc_monitor.MonitorLoop()
#     monitor_loop.subscribe_session(callback, None, GATEWAY_A, 5, token=get_rbac_token())
#     futures.wait({callback_fut}, timeout=0.2)

#     assert callback_fut.done() == True

# def test_monitorloop_session_callback_close(get_rbac_token):

#     callback_fut = None

#     def callback(*args, **kwargs):
#         callback_fut.set_result(True)

#     monitor_loop = fgc_monitor.MonitorLoop()
#     assert len(monitor_loop.session_data) == 0

#     # Assert subscription enabled
#     callback_fut = futures.Future()
#     handler = monitor_loop.subscribe_session(callback, None, GATEWAY_A, 5, token=get_rbac_token())
#     futures.wait({callback_fut}, timeout=0.2)
#     assert callback_fut.done() == True
#     assert len(monitor_loop.session_data) == 1

#     # Assert subscription disabled
#     monitor_loop.unsubscribe_session(handler)
#     callback_fut = futures.Future() # Restart future
#     futures.wait({callback_fut}, timeout=0.2)
#     assert callback_fut.done() == False
#     assert len(monitor_loop.session_data) == 0

# def test_monitorloop_session_callback_content(get_rbac_token):

#     callback_fut = futures.Future()

#     def callback(data, addr, curr_time):
#         callback_fut.set_result((data, addr, curr_time))

#     monitor_loop = fgc_monitor.MonitorLoop()
#     monitor_loop.subscribe_session(callback, None, GATEWAY_A, 5, token=get_rbac_token())
#     futures.wait({callback_fut}, timeout=0.2)

#     data, addr, curr_time = callback_fut.result(timeout=0)
#     assert isinstance(data, bytes)
#     assert isinstance(addr, tuple) and len(addr) == 2
#     assert isinstance(curr_time, float)

# def test_monitorloop_session_callback_timeout(get_rbac_token):

#     callback_fut = futures.Future()

#     def callback(data, addr, curr_time):
#         callback_fut.set_result((data, addr, curr_time))

#     monitor_loop = fgc_monitor.MonitorLoop()
#     monitor_loop.subscribe_session(callback, None, GATEWAY_A, 50, token=get_rbac_token(), timeout=0.1)
#     futures.wait({callback_fut}, timeout=0.2)

#     data, addr, curr_time = callback_fut.result(timeout=0)
#     assert data is None
#     assert addr is None
#     assert isinstance(curr_time, float)

# def test_monitorloop_shared_session_callback(get_rbac_token):

#     callback_fut_1 = futures.Future()
#     callback_fut_2 = futures.Future()

#     def callback(fut, data, addr, curr_time):
#         fut.set_result((data, addr, curr_time))

#     callback_1 = functools.partial(callback, callback_fut_1)
#     callback_2 = functools.partial(callback, callback_fut_2)

#     monitor_loop = fgc_monitor.MonitorLoop()
#     monitor_loop.subscribe_session(callback_1, None, GATEWAY_A, 5, token=get_rbac_token())
#     monitor_loop.subscribe_session(callback_2, None, GATEWAY_A, 5, token=get_rbac_token())
#     futures.wait({callback_fut_1, callback_fut_2}, timeout=0.2)

#     assert len(monitor_loop.session_data) == 1
#     data_1, addr_1, curr_time_1 = callback_fut_1.result(timeout=0)
#     data_2, addr_2, curr_time_2 = callback_fut_2.result(timeout=0)
#     assert data_1 is data_2
#     assert addr_1 is addr_2
#     assert curr_time_1 is curr_time_2

# def test_monitorloop_shared_session_callback_timeout(get_rbac_token):

#     callback_fut_1 = futures.Future()
#     callback_fut_2 = futures.Future()

#     def callback(fut, data, addr, curr_time):
#         fut.set_result((data, addr, curr_time))

#     callback_1 = functools.partial(callback, callback_fut_1)
#     callback_2 = functools.partial(callback, callback_fut_2)

#     monitor_loop = fgc_monitor.MonitorLoop()
#     monitor_loop.subscribe_session(callback_1, None, GATEWAY_A, 50, token=get_rbac_token(), timeout=0.1)
#     monitor_loop.subscribe_session(callback_2, None, GATEWAY_A, 5, token=get_rbac_token(), timeout=1.0)
#     futures.wait({callback_fut_1, callback_fut_2}, timeout=0.2)

#     data_1, addr_1, curr_time_1 = callback_fut_1.result(timeout=0)
#     data_2, addr_2, curr_time_2 = callback_fut_2.result(timeout=0)
#     assert data_1 is None and addr_1 is None
#     assert data_2 is not None and addr_2 is not None

# def test_monitorloop_shared_session_callback_close(get_rbac_token):

#     callback_fut_1 = futures.Future()
#     callback_fut_2 = futures.Future()

#     def callback_1(*args, **kwargs):
#         callback_fut_1.set_result(True)
#     def callback_2(*args, **kwargs):
#         callback_fut_2.set_result(True)

#     monitor_loop = fgc_monitor.MonitorLoop()

#     # Assert all subscriptions enabled
#     callback_fut_1 = futures.Future()
#     callback_fut_2 = futures.Future()
#     handler_1 = monitor_loop.subscribe_session(callback_1, None, GATEWAY_A, 5, token=get_rbac_token())
#     handler_2 = monitor_loop.subscribe_session(callback_2, None, GATEWAY_A, 5, token=get_rbac_token())
#     futures.wait({callback_fut_1, callback_fut_2}, timeout=0.2)
#     assert callback_fut_1.done() == True
#     assert callback_fut_2.done() == True
#     assert len(monitor_loop.session_data) == 1

#     # Assert subscription 1 disabled, subscription 2 enabled
#     monitor_loop.unsubscribe_session(handler_1)
#     callback_fut_1 = futures.Future() # Restart future
#     callback_fut_2 = futures.Future() # Restart future
#     futures.wait({callback_fut_1, callback_fut_2}, timeout=0.2)
#     assert callback_fut_1.done() == False
#     assert callback_fut_2.done() == True
#     assert len(monitor_loop.session_data) == 1

#     # Assert all subscriptions disabled
#     monitor_loop.unsubscribe_session(handler_2)
#     callback_fut_1 = futures.Future() # Restart future
#     callback_fut_2 = futures.Future() # Restart future
#     futures.wait({callback_fut_1, callback_fut_2}, timeout=0.2)
#     assert callback_fut_1.done() == False
#     assert callback_fut_2.done() == False
#     assert len(monitor_loop.session_data) == 0

# def test_monitorloop_non_shared_session_callback(get_rbac_token):

#     callback_fut_1 = futures.Future()
#     callback_fut_2 = futures.Future()

#     def callback(fut, data, addr, curr_time):
#         fut.set_result((data, addr, curr_time))

#     callback_1 = functools.partial(callback, callback_fut_1)
#     callback_2 = functools.partial(callback, callback_fut_2)

#     monitor_loop = fgc_monitor.MonitorLoop()
#     monitor_loop.subscribe_session(callback_1, None, GATEWAY_A, 5, token=get_rbac_token())
#     monitor_loop.subscribe_session(callback_2, None, GATEWAY_B, 5, token=get_rbac_token())
#     futures.wait({callback_fut_1, callback_fut_2}, timeout=0.2)

#     assert len(monitor_loop.session_data) == 2
#     data_1, addr_1, _ = callback_fut_1.result(timeout=0)
#     data_2, addr_2, _ = callback_fut_2.result(timeout=0)
#     assert data_1 is not data_2
#     assert addr_1 is not addr_2

# def test_monitorloop_non_shared_session_callback_close(get_rbac_token):

#     callback_fut_1 = futures.Future()
#     callback_fut_2 = futures.Future()

#     def callback_1(*args, **kwargs):
#         callback_fut_1.set_result(True)
#     def callback_2(*args, **kwargs):
#         callback_fut_2.set_result(True)

#     monitor_loop = fgc_monitor.MonitorLoop()

#     # Assert all subscriptions enabled
#     callback_fut_1 = futures.Future()
#     callback_fut_2 = futures.Future()
#     handler_1 = monitor_loop.subscribe_session(callback_1, None, GATEWAY_A, 5, token=get_rbac_token())
#     handler_2 = monitor_loop.subscribe_session(callback_2, None, GATEWAY_B, 5, token=get_rbac_token())
#     futures.wait({callback_fut_1, callback_fut_2}, timeout=0.2)
#     assert callback_fut_1.done() == True
#     assert callback_fut_2.done() == True
#     assert len(monitor_loop.session_data) == 2

#     # Assert subscription 1 disabled, subscription 2 enabled
#     monitor_loop.unsubscribe_session(handler_1)
#     callback_fut_1 = futures.Future() # Restart future
#     callback_fut_2 = futures.Future() # Restart future
#     futures.wait({callback_fut_1, callback_fut_2}, timeout=0.2)
#     assert callback_fut_1.done() == False
#     assert callback_fut_2.done() == True
#     assert len(monitor_loop.session_data) == 1

#     # Assert all subscriptions disabled
#     monitor_loop.unsubscribe_session(handler_2)
#     callback_fut_1 = futures.Future() # Restart future
#     callback_fut_2 = futures.Future() # Restart future
#     futures.wait({callback_fut_1, callback_fut_2}, timeout=0.2)
#     assert callback_fut_1.done() == False
#     assert callback_fut_2.done() == False
#     assert len(monitor_loop.session_data) == 0

# def test_monitorloop_port_callback(get_rbac_token):

#     callback_fut = futures.Future()

#     def callback(*args, **kwargs):
#         callback_fut.set_result(True)

#     monitor_loop = fgc_monitor.MonitorLoop()

#     with new_udp_stream(GATEWAY_A, 5, 12345, 0x0000, token=get_rbac_token()):
#         monitor_loop.subscribe_port(callback, None, 12345)
#         futures.wait({callback_fut}, timeout=0.2)

#     assert callback_fut.done() == True

# def test_monitorloop_port_callback_close(get_rbac_token):

#     callback_fut = None

#     def callback(*args, **kwargs):
#         callback_fut.set_result(True)

#     monitor_loop = fgc_monitor.MonitorLoop()

#     with new_udp_stream(GATEWAY_A, 5, 12345, 0x0000, token=get_rbac_token()):

#         # Assert subscription enabled
#         callback_fut = futures.Future()
#         handler = monitor_loop.subscribe_port(callback, None, 12345)
#         futures.wait({callback_fut}, timeout=0.2)
#         assert callback_fut.done() == True
#         assert len(monitor_loop.session_data) == 1

#         # Assert subscription disabled
#         monitor_loop.unsubscribe_port(handler)
#         callback_fut = futures.Future() # Restart future
#         futures.wait({callback_fut}, timeout=0.2)
#         assert callback_fut.done() == False
#         assert len(monitor_loop.session_data) == 0

# def test_monitorloop_port_callback_content(get_rbac_token):

#     callback_fut = futures.Future()

#     def callback(data, addr, curr_time):
#         callback_fut.set_result((data, addr, curr_time))

#     monitor_loop = fgc_monitor.MonitorLoop()

#     with new_udp_stream(GATEWAY_A, 5, 12345, 0x0000, token=get_rbac_token()):

#         monitor_loop.subscribe_port(callback, None, 12345)
#         futures.wait({callback_fut}, timeout=0.2)

#         data, addr, curr_time = callback_fut.result(timeout=0)
#         assert isinstance(data, bytes)
#         assert isinstance(addr, tuple) and len(addr) == 2
#         assert isinstance(curr_time, float)

# def test_monitorloop_port_callback_timeout(get_rbac_token):

#     callback_fut = futures.Future()

#     def callback(data, addr, curr_time):
#         callback_fut.set_result((data, addr, curr_time))

#     monitor_loop = fgc_monitor.MonitorLoop()

#     with new_udp_stream(GATEWAY_A, 50, 12345, 0x0000, token=get_rbac_token()):

#         monitor_loop.subscribe_port(callback, None, 12345, timeout=0.1)
#         futures.wait({callback_fut}, timeout=0.2)

#     data, addr, curr_time = callback_fut.result(timeout=0)
#     assert data is None
#     assert addr is None
#     assert isinstance(curr_time, float)

# def test_monitorloop_shared_port_callback(get_rbac_token):

#     callback_fut_1 = futures.Future()
#     callback_fut_2 = futures.Future()

#     def callback(fut, data, addr, curr_time):
#         fut.set_result((data, addr, curr_time))

#     callback_1 = functools.partial(callback, callback_fut_1)
#     callback_2 = functools.partial(callback, callback_fut_2)

#     monitor_loop = fgc_monitor.MonitorLoop()

#     with new_udp_stream(GATEWAY_A, 5, 12345, 0x0000, token=get_rbac_token()):

#         monitor_loop.subscribe_port(callback_1, None, 12345)
#         monitor_loop.subscribe_port(callback_2, None, 12345)
#         futures.wait({callback_fut_1, callback_fut_2}, timeout=0.2)

#         assert len(monitor_loop.session_data) == 1
#         data_1, addr_1, curr_time_1 = callback_fut_1.result(timeout=0)
#         data_2, addr_2, curr_time_2 = callback_fut_2.result(timeout=0)
#         assert data_1 is data_2
#         assert addr_1 is addr_2
#         assert curr_time_1 is curr_time_2

# def test_monitorloop_shared_port_callback_close(get_rbac_token):

#     callback_fut_1 = futures.Future()
#     callback_fut_2 = futures.Future()

#     def callback_1(*args, **kwargs):
#         callback_fut_1.set_result(True)
#     def callback_2(*args, **kwargs):
#         callback_fut_2.set_result(True)

#     monitor_loop = fgc_monitor.MonitorLoop()

#     with new_udp_stream(GATEWAY_A, 5, 12345, 0x0000, token=get_rbac_token()):

#         # Assert all subscriptions enabled
#         callback_fut_1 = futures.Future()
#         callback_fut_2 = futures.Future()
#         handler_1 = monitor_loop.subscribe_port(callback_1, None, 12345)
#         handler_2 = monitor_loop.subscribe_port(callback_2, None, 12345)
#         futures.wait({callback_fut_1, callback_fut_2}, timeout=0.2)
#         assert callback_fut_1.done() == True
#         assert callback_fut_2.done() == True
#         assert len(monitor_loop.session_data) == 1

#         # Assert subscription 1 disabled, subscription 2 enabled
#         monitor_loop.unsubscribe_port(handler_1)
#         callback_fut_1 = futures.Future() # Restart future
#         callback_fut_2 = futures.Future() # Restart future
#         futures.wait({callback_fut_1, callback_fut_2}, timeout=0.2)
#         assert callback_fut_1.done() == False
#         assert callback_fut_2.done() == True
#         assert len(monitor_loop.session_data) == 1

#         # Assert all subscriptions disabled
#         monitor_loop.unsubscribe_port(handler_2)
#         callback_fut_1 = futures.Future() # Restart future
#         callback_fut_2 = futures.Future() # Restart future
#         futures.wait({callback_fut_1, callback_fut_2}, timeout=0.2)
#         assert callback_fut_1.done() == False
#         assert callback_fut_2.done() == False
#         assert len(monitor_loop.session_data) == 0

# def test_monitorloop_non_shared_port_callback(get_rbac_token):

#     callback_fut_1 = futures.Future()
#     callback_fut_2 = futures.Future()

#     def callback(fut, data, addr, curr_time):
#         fut.set_result((data, addr, curr_time))

#     callback_1 = functools.partial(callback, callback_fut_1)
#     callback_2 = functools.partial(callback, callback_fut_2)

#     monitor_loop = fgc_monitor.MonitorLoop()

#     with new_udp_stream(GATEWAY_A, 5, 12345, 0x0000, token=get_rbac_token()), new_udp_stream(GATEWAY_B, 5, 12346, 0x0000, token=get_rbac_token()):

#         monitor_loop.subscribe_port(callback_1, None, 12345)
#         monitor_loop.subscribe_port(callback_2, None, 12346)
#         futures.wait({callback_fut_1, callback_fut_2}, timeout=0.2)

#         assert len(monitor_loop.session_data) == 2
#         data_1, addr_1, _ = callback_fut_1.result(timeout=0)
#         data_2, addr_2, _ = callback_fut_2.result(timeout=0)
#         assert data_1 is not data_2
#         assert addr_1 is not addr_2

# def test_monitorloop_non_shared_port_callback_timeout(get_rbac_token):

#     callback_fut_1 = futures.Future()
#     callback_fut_2 = futures.Future()

#     def callback(fut, data, addr, curr_time):
#         fut.set_result((data, addr, curr_time))

#     callback_1 = functools.partial(callback, callback_fut_1)
#     callback_2 = functools.partial(callback, callback_fut_2)

#     monitor_loop = fgc_monitor.MonitorLoop()

#     with new_udp_stream(GATEWAY_A, 50, 12345, 0x0000, token=get_rbac_token()), new_udp_stream(GATEWAY_A, 5, 12346, 0x0000, token=get_rbac_token()):

#         monitor_loop.subscribe_port(callback_1, None, 12345, timeout=0.1)
#         monitor_loop.subscribe_port(callback_2, None, 12346, timeout=1.0)
#         futures.wait({callback_fut_1, callback_fut_2}, timeout=0.2)

#     data_1, addr_1, curr_time_1 = callback_fut_1.result(timeout=0)
#     data_2, addr_2, curr_time_2 = callback_fut_2.result(timeout=0)
#     assert data_1 is None and addr_1 is None
#     assert data_2 is not None and addr_2 is not None

# def test_monitorloop_non_shared_port_callback_close(get_rbac_token):

#     callback_fut_1 = futures.Future()
#     callback_fut_2 = futures.Future()

#     def callback_1(*args, **kwargs):
#         callback_fut_1.set_result(True)
#     def callback_2(*args, **kwargs):
#         callback_fut_2.set_result(True)

#     monitor_loop = fgc_monitor.MonitorLoop()

#     with new_udp_stream(GATEWAY_A, 5, 12345, 0x0000, token=get_rbac_token()), new_udp_stream(GATEWAY_B, 5, 12346, 0x0000, token=get_rbac_token()):

#         # Assert all subscriptions enabled
#         callback_fut_1 = futures.Future()
#         callback_fut_2 = futures.Future()
#         handler_1 = monitor_loop.subscribe_port(callback_1, None, 12345)
#         handler_2 = monitor_loop.subscribe_port(callback_2, None, 12346)
#         futures.wait({callback_fut_1, callback_fut_2}, timeout=0.2)
#         assert callback_fut_1.done() == True
#         assert callback_fut_2.done() == True
#         assert len(monitor_loop.session_data) == 2

#         # Assert subscription 1 disabled, subscription 2 enabled
#         monitor_loop.unsubscribe_port(handler_1)
#         callback_fut_1 = futures.Future() # Restart future
#         callback_fut_2 = futures.Future() # Restart future
#         futures.wait({callback_fut_1, callback_fut_2}, timeout=0.2)
#         assert callback_fut_1.done() == False
#         assert callback_fut_2.done() == True
#         assert len(monitor_loop.session_data) == 1

#         # Assert all subscriptions disabled
#         monitor_loop.unsubscribe_port(handler_2)
#         callback_fut_1 = futures.Future() # Restart future
#         callback_fut_2 = futures.Future() # Restart future
#         futures.wait({callback_fut_1, callback_fut_2}, timeout=0.2)
#         assert callback_fut_1.done() == False
#         assert callback_fut_2.done() == False
#         assert len(monitor_loop.session_data) == 0

# def test_monitorloop_subscribe_session_error(get_rbac_token):
#     monitor_loop = fgc_monitor.MonitorLoop()
#     err_fut = futures.Future()

#     def callback(*args, **kwargs):
#         pass

#     def callback_err(*args, **kwargs):
#         err_fut.set_exception(args[0])

#     monitor_loop.subscribe_session(callback, callback_err, GATEWAY_ERR, 5, token=get_rbac_token())

#     with pytest.raises(socket.gaierror):
#         err_fut.result(timeout=1.0)

# def test_monitorloop_subscribe_port_error():
#     monitor_loop = fgc_monitor.MonitorLoop()
#     err_fut = futures.Future()

#     def callback(*args, **kwargs):
#         pass

#     def callback_err(*args, **kwargs):
#         err_fut.set_exception(args[0])

#     monitor_loop.subscribe_port(callback, callback_err, 7) # Port 7 is reserved for Echo protocol

#     with pytest.raises(PermissionError):
#         err_fut.result(timeout=1.0)

# def test_monitorloop_session_error(get_rbac_token, monkeypatch):
#     fut = futures.Future()
#     err_fut = futures.Future()

#     def callback(*args, **kwargs):
#         fut.set_result(None)
#     def callback_err(err, err_time):
#         err_fut.set_result(err)

#     monkeypatch.setattr(fgc_monitor, "RETRY_CONNECTION_MARGIN", 0.01)
#     monkeypatch.setattr(fgc_monitor, "RETRY_CONNECTION_PERIOD", 0.01)

#     monitor_loop = fgc_monitor.MonitorLoop()
#     handler = monitor_loop.subscribe_session(callback, callback_err, GATEWAY_A, 5, token=get_rbac_token())
#     futures.wait({fut}, timeout=0.5)
#     handler.session.tcp_socket.close()
#     futures.wait({err_fut}, timeout=0.5)

#     assert err_fut.done()
#     assert isinstance(err_fut.result(), RuntimeError)
#     assert 'timeout' in str(err_fut.result())

# def test_monitorloop_session_error_recover(get_rbac_token, monkeypatch):

#     ok_fut_1 = futures.Future()
#     err_fut_2 = futures.Future()
#     ok_fut_3 = futures.Future()

#     def callback(data, addr, curr_time):
#         if err_fut_2.done():
#             ok_fut_3.set_result(curr_time)
#         else:
#             ok_fut_1.set_result(curr_time)
#     def callback_err(err, err_time):
#         err_fut_2.set_result(err_time)

#     monkeypatch.setattr(fgc_monitor, "RETRY_CONNECTION_MARGIN", 0.01)
#     monkeypatch.setattr(fgc_monitor, "RETRY_CONNECTION_PERIOD", 0.01)

#     monitor_loop = fgc_monitor.MonitorLoop()
#     handler = monitor_loop.subscribe_session(callback, callback_err, GATEWAY_A, 5, token=get_rbac_token())

#     futures.wait({ok_fut_1}, timeout=0.5)

#     prev_tcp_socket = handler.session.tcp_socket
#     prev_udp_socket = handler.session.udp_socket
#     handler.session.tcp_socket.close()

#     futures.wait({err_fut_2, ok_fut_3}, timeout=0.5)

#     assert err_fut_2.done()
#     assert ok_fut_3.done()
#     assert handler.session.active
#     assert handler.session.tcp_socket and handler.session.tcp_socket != prev_tcp_socket
#     assert handler.session.udp_socket and handler.session.udp_socket != prev_udp_socket

#     time_2_err = err_fut_2.result()
#     time_3_ok = ok_fut_3.result()
#     assert time_3_ok > time_2_err

# def test_monitorloop_session_error_recover_period(get_rbac_token, monkeypatch):

#     fut = futures.Future()
#     err_fut = futures.Future()
#     retry_timestamps = []

#     def callback(data, addr, curr_time):
#         fut.set_result(curr_time)
#     def callback_err(err, err_time):
#         monkeypatch.setattr(session, "sub_address", GATEWAY_ERR)
#         def foo():
#             retry_timestamps.append(time.time())
#         monkeypatch.setattr(session, "start", foo)

#     monkeypatch.setattr(fgc_monitor, "RETRY_CONNECTION_MARGIN", 0.01)
#     monkeypatch.setattr(fgc_monitor, "RETRY_CONNECTION_PERIOD", 0.2)

#     monitor_loop = fgc_monitor.MonitorLoop()
#     handler = monitor_loop.subscribe_session(callback, callback_err, GATEWAY_A, 5, token=get_rbac_token())

#     futures.wait({fut}, timeout=0.5)
#     session = handler.session
#     session.tcp_socket.close()

#     futures.wait({err_fut}, timeout=1.0)

#     assert len(retry_timestamps) > 1
#     for i in range(1, len(retry_timestamps)):
#         assert (retry_timestamps[i] - retry_timestamps[i-1]) == pytest.approx(0.2, abs=0.02)

# # Test MonitorSession

# def test_hostname_resolution():
#     ip_expected = socket.gethostbyname(GATEWAY_A)
#     ips_resolved = fgc_monitor.resolve_hostnames({GATEWAY_A})
#     assert ip_expected == ips_resolved[GATEWAY_A]

# def test_hostname_resolution_caching(monkeypatch):

#     call_counter = 0
#     def foo(addr):
#         nonlocal call_counter
#         call_counter += 1
#         return addr

#     monkeypatch.setattr(fgc_monitor, "hostname_to_ip", dict())
#     monkeypatch.setattr(socket, "gethostbyname", foo)

#     ip_a_1 = fgc_monitor.resolve_hostnames({GATEWAY_A})
#     ip_a_2 = fgc_monitor.resolve_hostnames({GATEWAY_A})
#     assert call_counter == 1
#     assert ip_a_1[GATEWAY_A] == ip_a_2[GATEWAY_A]

#     ip_b_1 = fgc_monitor.resolve_hostnames({GATEWAY_B})
#     ip_b_2 = fgc_monitor.resolve_hostnames({GATEWAY_B})

#     assert call_counter == 2
#     assert ip_b_1[GATEWAY_B] == ip_b_2[GATEWAY_B]

#     ip_ab = fgc_monitor.resolve_hostnames({GATEWAY_A, GATEWAY_B})

#     assert call_counter == 2
#     assert ip_ab[GATEWAY_A] != ip_ab[GATEWAY_B]

# def test_ip_resolution():
#     ip = socket.gethostbyname(GATEWAY_A)
#     address_resolved = fgc_monitor.resolve_ips({ip})
#     assert GATEWAY_A.lower() == address_resolved[ip].lower()

# def test_ip_resolution_caching(monkeypatch):

#     ip_a = socket.gethostbyname(GATEWAY_A)
#     ip_b = socket.gethostbyname(GATEWAY_B)

#     call_counter = 0
#     def foo(addr):
#         nonlocal call_counter
#         call_counter += 1
#         return (addr, None, None)

#     monkeypatch.setattr(fgc_monitor, "ip_to_hostname", dict())
#     monkeypatch.setattr(socket, "gethostbyaddr", foo)

#     a_1 = fgc_monitor.resolve_ips({ip_a})
#     a_2 = fgc_monitor.resolve_ips({ip_a})
#     assert call_counter == 1
#     assert a_1[ip_a] == a_2[ip_a]

#     b_1 = fgc_monitor.resolve_ips({ip_b})
#     b_2 = fgc_monitor.resolve_ips({ip_b})

#     assert call_counter == 2
#     assert b_1[ip_b] == b_2[ip_b]

#     ab = fgc_monitor.resolve_hostnames({ip_a, ip_b})

#     assert call_counter == 2
#     assert ab[ip_a] != ab[ip_b]

# def test_decode_data(monkeypatch, reload_namefile):

#     dummy_data = dict()
#     dummy_timestamp = 12345

#     def foo(data):
#         return [object() for _ in range(65)]

#     monkeypatch.setattr(fgc_monitor, "decode", foo)

#     data_dict, data_list = fgc_monitor.decode_data(GATEWAY_A.lower(), dummy_timestamp, dummy_data)

#     assert isinstance(data_dict, dict)
#     assert isinstance(data_list, list)
#     assert DEVICE_A1 in data_dict
#     assert DEVICE_A2 in data_dict
#     assert data_dict[DEVICE_A1] in data_list
#     assert data_dict[DEVICE_A2] in data_list
#     assert data_dict[DEVICE_A1] != data_dict[DEVICE_A2]

# def test_decode_data_caching(monkeypatch, reload_namefile):

#     dummy_data = dict()
#     dummy_timestamp_1 = 12346
#     dummy_timestamp_2 = 12347
#     call_count = 0

#     def foo(data):
#         nonlocal call_count
#         call_count += 1
#         return [object() for _ in range(65)]

#     monkeypatch.setattr(fgc_monitor, "decode", foo)

#     data_dict_a1, data_list_a1 = fgc_monitor.decode_data(GATEWAY_A.lower(), dummy_timestamp_1, dummy_data)
#     data_dict_a2, data_list_a2 = fgc_monitor.decode_data(GATEWAY_A.lower(), dummy_timestamp_1, dummy_data)

#     assert call_count == 1
#     assert data_dict_a1 is data_dict_a2
#     assert data_list_a1 is data_list_a2

#     data_dict_b1, data_list_b1 = fgc_monitor.decode_data(GATEWAY_B.lower(), dummy_timestamp_1, dummy_data)
#     fgc_monitor.decode_data(GATEWAY_B.lower(), dummy_timestamp_1, dummy_data)

#     assert call_count == 2
#     assert data_dict_a1 is not data_dict_b1

#     data_dict_a3, data_list_a3 = fgc_monitor.decode_data(GATEWAY_A.lower(), dummy_timestamp_2, dummy_data)
#     fgc_monitor.decode_data(GATEWAY_A.lower(), dummy_timestamp_2, dummy_data)

#     assert call_count == 3
#     assert data_dict_a1 is not data_dict_a3

# def test_monitor_session_start_stop(get_rbac_token):

#     def foo(*args, **kwargs):
#         fut.set_result(True)

#     m_session = fgc_monitor.MonitorSession(foo, GATEWAY_A, 5, rbac_token=get_rbac_token())

#     fut = futures.Future()
#     m_session.start()
#     futures.wait({fut}, timeout=0.2)
#     assert fut.done()

#     fut = futures.Future()
#     m_session.stop()
#     futures.wait({fut}, timeout=0.2)
#     assert not fut.done()

# def test_monitor_session_context(get_rbac_token):

#     def foo(*args, **kwargs):
#         fut.set_result(True)

#     fut = futures.Future()
#     with fgc_monitor.MonitorSession(foo, GATEWAY_A, 5, rbac_token=get_rbac_token()):
#         futures.wait({fut}, timeout=0.2)
#         assert fut.done()

#     fut = futures.Future()
#     futures.wait({fut}, timeout=0.2)
#     assert not fut.done()

# def test_monitor_session_callback(get_rbac_token):

#     fut = futures.Future()

#     def foo(data_dict, data_list, gateway, curr_time):
#         fut.set_result((data_dict, data_list, gateway, curr_time))

#     with fgc_monitor.MonitorSession(foo, GATEWAY_A, 5, rbac_token=get_rbac_token()):
#         futures.wait({fut}, timeout=0.2)

#     data_dict, data_list, gateway, curr_time = fut.result()

#     assert isinstance(data_dict, dict)
#     assert isinstance(data_list, list)
#     assert gateway.lower() == GATEWAY_A.lower()

#     assert DEVICE_A1 in data_dict
#     assert DEVICE_A2 in data_dict
#     assert data_dict[DEVICE_A1] in data_list
#     assert data_dict[DEVICE_A2] in data_list

# def test_monitor_session_callback_multiple_dev_same_gw(get_rbac_token):

#     fut = futures.Future()

#     def foo(data_dict, data_list, gateway, curr_time):
#         fut.set_result((data_dict, data_list, gateway, curr_time))

#     with fgc_monitor.MonitorSession(foo, {DEVICE_A1, DEVICE_A2}, 5, rbac_token=get_rbac_token()):
#         futures.wait({fut}, timeout=0.2)

#     data_dict, data_list, gateway, curr_time = fut.result()

#     assert isinstance(data_dict, dict)
#     assert isinstance(data_list, list)
#     assert gateway.lower() == GATEWAY_A.lower()

#     assert DEVICE_A1 in data_dict
#     assert DEVICE_A2 in data_dict
#     assert data_dict[DEVICE_A1] in data_list
#     assert data_dict[DEVICE_A2] in data_list

# def test_monitor_session_callback_multiple_dev_multiple_gw(get_rbac_token):

#     fut_a = futures.Future()
#     fut_b = futures.Future()

#     def foo(data_dict, data_list, gateway, curr_time):
#         if gateway.lower() == GATEWAY_A.lower():
#             fut_a.set_result((data_dict, data_list, gateway, curr_time))
#         if gateway.lower() == GATEWAY_B.lower():
#             fut_b.set_result((data_dict, data_list, gateway, curr_time))

#     with fgc_monitor.MonitorSession(foo, {DEVICE_A1, DEVICE_B1}, 5, rbac_token=get_rbac_token()):
#         futures.wait({fut_a, fut_b}, timeout=0.2)

#     assert fut_a.done()
#     assert fut_b.done()

#     data_dict_a, data_list_a, gateway_a, curr_time_a = fut_a.result()
#     data_dict_b, data_list_b, gateway_b, curr_time_b = fut_b.result()

#     assert DEVICE_A1 in data_dict_a
#     assert DEVICE_B1 in data_dict_b
#     assert DEVICE_A1 not in data_dict_b
#     assert DEVICE_B1 not in data_dict_a
#     assert gateway_a != gateway_b

# def test_monitor_session_multiple_callback_same_gw(get_rbac_token):

#     fut_1 = futures.Future()
#     fut_2 = futures.Future()

#     def foo_1(data_dict, data_list, gateway, curr_time):
#         fut_1.set_result((data_dict, data_list, gateway, curr_time))
#     def foo_2(data_dict, data_list, gateway, curr_time):
#         fut_2.set_result((data_dict, data_list, gateway, curr_time))

#     session_1 = fgc_monitor.MonitorSession(foo_1, DEVICE_A1, 5, rbac_token=get_rbac_token())
#     session_2 = fgc_monitor.MonitorSession(foo_2, DEVICE_A2, 5, rbac_token=get_rbac_token())
#     session_1.start()
#     session_2.start()
#     futures.wait({fut_1, fut_2}, timeout=0.2)

#     data_dict_1, data_list_1, gateway_1, curr_time_1 = fut_1.result()
#     data_dict_2, data_list_2, gateway_2, curr_time_2 = fut_2.result()

#     assert curr_time_1 == curr_time_2
#     assert data_dict_1 is data_dict_2
#     assert data_list_1 is data_list_2
#     assert gateway_1 == gateway_2

#     assert DEVICE_A1 in data_dict_1
#     assert DEVICE_A2 in data_dict_1

# def test_monitor_session_callback_err(monkeypatch, get_rbac_token):

#     fut = futures.Future()
#     fut_err = futures.Future()

#     def foo(*args, **kwargs):
#         fut.set_result(None)
#     def foo_err(err, gateway, curr_time):
#         fut_err.set_result((err, gateway, curr_time))

#     monkeypatch.setattr(fgc_monitor, "RETRY_CONNECTION_MARGIN", 0.01)

#     with fgc_monitor.MonitorSession(foo, GATEWAY_A, 1, callback_err=foo_err, rbac_token=get_rbac_token()) as session:
#         # Close TCP socket, will cause an error
#         fut.result(timeout=0.5)
#         for s_handler in session.subscription_handlers:
#             s_handler.session.tcp_socket.close()

#         futures.wait({fut_err}, timeout=0.2)
#         assert fut_err.done()

#     err, gateway, err_time = fut_err.result()
#     assert isinstance(err, RuntimeError)
#     assert isinstance(err_time, float)

# def test_monitor_session_period(get_rbac_token):

#     fut = futures.Future()
#     calls = []

#     def foo(data_dict, data_list, gateway, curr_time):
#         calls.append(curr_time)
#         if len(calls) >= 5:
#             fut.set_result(True)

#     with fgc_monitor.MonitorSession(foo, GATEWAY_A, 2, rbac_token=get_rbac_token()):
#         futures.wait({fut}, timeout=0.5)

#     assert fut.done()
#     for i in range(1, len(calls)):
#         time_diff = calls[i] - calls[i-1]
#         assert time_diff == pytest.approx(0.04, abs=0.005)

# #def test_monitor_session_timeout_period(monkeypatch, get_rbac_token):
# #
# #    fut = futures.Future()
# #    calls = []
# #
# #    def foo(data_dict, data_list, gateway, curr_time):
# #        calls.append(curr_time)
# #        if len(calls) >= 5:
# #            fut.set_result(True)
# #
# #    monkeypatch.setattr(fgc_monitor, "RETRY_CONNECTION_MARGIN", 10.0) # Margin big enouth to trigger timeouts
# #    with fgc_monitor.MonitorSession(foo, GATEWAY_A, 5, timeout = 0.02, rbac_token=get_rbac_token()) as session:
# #        # Close TCP socket, will cause an error
# #        for s_handler in session.subscription_handlers:
# #            s_handler.session.tcp_socket.close()
# #        futures.wait({fut}, timeout=0.5)
# #
# #    assert fut.done()
# #    for i in range(1, len(calls)):
# #        time_diff = calls[i] - calls[i-1]
# #        assert time_diff == pytest.approx(0.02 + fgc_monitor.FGC_CYCLE_TIME, abs=0.005)


# def test_monitor_session_timeout(monkeypatch, get_rbac_token):

#     fut_ok = futures.Future()
#     fut_timeout = futures.Future()

#     def foo(data_dict, data_list, gateway, curr_time):
#         if data_dict or data_list:
#             fut_ok.set_result(None)
#         else:
#             fut_timeout.set_result((data_dict, data_list, gateway, curr_time))

#     monkeypatch.setattr(fgc_monitor, "RETRY_CONNECTION_MARGIN", 10.0) # Margin big enouth to trigger timeouts
#     with fgc_monitor.MonitorSession(foo, GATEWAY_A, 5, timeout=0.02, rbac_token=get_rbac_token()) as session:
#         # Close TCP socket, will cause an error
#         futures.wait({fut_ok}, timeout=0.5)
#         for s_handler in session.subscription_handlers:
#             s_handler.session.tcp_socket.close()
#         futures.wait({fut_timeout}, timeout=0.2)

#     assert fut_timeout.done()
#     data_dict, data_list, gateway, curr_time = fut_timeout.result()
#     assert data_dict is None
#     assert data_list is None
#     assert gateway.lower() == GATEWAY_A.lower()
#     assert isinstance(curr_time, float)

# ####

# def test_monitor_port_start_stop(get_rbac_token):

#     def foo(*args, **kwargs):
#         fut.set_result(True)

#     fut = futures.Future()
#     with new_udp_stream(GATEWAY_A, 5, 12345, 0, token=get_rbac_token()):
#         m_session = fgc_monitor.MonitorPort(foo, 12345)
#         m_session.start()
#         futures.wait({fut}, timeout=0.2)

#         assert fut.done()
#         m_session.stop()
#         fut = futures.Future()
#         futures.wait({fut}, timeout=0.2)
#         assert not fut.done()

# def test_monitor_port_context(get_rbac_token):

#     def foo(*args, **kwargs):
#         fut.set_result(True)

#     fut = futures.Future()
#     with new_udp_stream(GATEWAY_A, 5, 12345, 0, token=get_rbac_token()):
#         with fgc_monitor.MonitorPort(foo, 12345):
#             futures.wait({fut}, timeout=0.2)

#     assert fut.done()
#     fut = futures.Future()
#     futures.wait({fut}, timeout=0.2)
#     assert not fut.done()

# def test_monitor_port_callback(get_rbac_token):

#     fut = futures.Future()

#     def foo(data_dict, data_list, gateway, curr_time):
#         fut.set_result((data_dict, data_list, gateway, curr_time))

#     with new_udp_stream(GATEWAY_A, 5, 12345, 0, token=get_rbac_token()):
#         with fgc_monitor.MonitorPort(foo, 12345):
#             futures.wait({fut}, timeout=0.2)

#     data_dict, data_list, gateway, curr_time = fut.result()

#     assert isinstance(data_dict, dict)
#     assert isinstance(data_list, list)
#     assert gateway.lower() == GATEWAY_A.lower()

#     assert DEVICE_A1 in data_dict
#     assert DEVICE_A2 in data_dict
#     assert data_dict[DEVICE_A1] in data_list
#     assert data_dict[DEVICE_A2] in data_list

# def test_monitor_port_callback_multiple_gw(get_rbac_token):

#     fut_a = futures.Future()
#     fut_b = futures.Future()

#     def foo(data_dict, data_list, gateway, curr_time):
#         if gateway == GATEWAY_A.lower():
#             fut_a.set_result((data_dict, data_list, gateway, curr_time))
#         if gateway == GATEWAY_B.lower():
#             fut_b.set_result((data_dict, data_list, gateway, curr_time))

#     with new_udp_stream(GATEWAY_A, 5, 12345, 0, token=get_rbac_token()), new_udp_stream(GATEWAY_B, 5, 12345, 0, token=get_rbac_token()):
#         with fgc_monitor.MonitorPort(foo, 12345):
#             futures.wait({fut_a, fut_b}, timeout=0.2)

#     assert fut_a.done()
#     assert fut_b.done()

#     data_dict_a, data_list_a, gateway_a, curr_time_a = fut_a.result()
#     data_dict_b, data_list_b, gateway_b, curr_time_b = fut_b.result()

#     assert DEVICE_A1 in data_dict_a
#     assert DEVICE_B1 in data_dict_b
#     assert DEVICE_A1 not in data_dict_b
#     assert DEVICE_B1 not in data_dict_a
#     assert curr_time_a != curr_time_b

# def test_monitor_port_multiple_callback_same_gw(get_rbac_token):

#     fut_1 = futures.Future()
#     fut_2 = futures.Future()

#     def foo_1(data_dict, data_list, gateway, curr_time):
#         fut_1.set_result((data_dict, data_list, gateway, curr_time))
#     def foo_2(data_dict, data_list, gateway, curr_time):
#         fut_2.set_result((data_dict, data_list, gateway, curr_time))

#     with new_udp_stream(GATEWAY_A, 5, 12345, 0, token=get_rbac_token()):
#         session_1 = fgc_monitor.MonitorPort(foo_1, 12345)
#         session_2 = fgc_monitor.MonitorPort(foo_2, 12345)
#         session_1.start()
#         session_2.start()
#         futures.wait({fut_1, fut_2}, timeout=0.2)

#     data_dict_1, data_list_1, gateway_1, curr_time_1 = fut_1.result()
#     data_dict_2, data_list_2, gateway_2, curr_time_2 = fut_2.result()

#     assert curr_time_1 == curr_time_2
#     assert data_dict_1 is data_dict_2
#     assert data_list_1 is data_list_2
#     assert gateway_1 == gateway_2

#     assert DEVICE_A1 in data_dict_1
#     assert DEVICE_A2 in data_dict_1

# def test_monitor_port_callback_err(monkeypatch, get_rbac_token):

#     fut_err = futures.Future()

#     def foo(*args, **kwargs):
#         raise RuntimeError("Boo!")
#     def foo_err(err, gateway, curr_time):
#         fut_err.set_result((err, gateway, curr_time))

#     monkeypatch.setattr(fgc_monitor, "RETRY_CONNECTION_MARGIN", 0.01)

#     with new_udp_stream(GATEWAY_A, 5, 12345, 0, token=get_rbac_token()):
#         with fgc_monitor.MonitorPort(foo, 12345, callback_err=foo_err) as session:
#             futures.wait({fut_err}, timeout=0.2)

#     assert fut_err.done()
#     err, gateway, err_time = fut_err.result()
#     assert isinstance(err, RuntimeError)
#     assert isinstance(err_time, float)

# def test_monitor_port_timeout(monkeypatch, get_rbac_token):

#     fut = futures.Future()

#     def foo(data_dict, data_list, gateway, curr_time):
#         fut.set_result((data_dict, data_list, gateway, curr_time))

#     monkeypatch.setattr(fgc_monitor, "RETRY_CONNECTION_MARGIN", 10.0) # Margin big enouth to trigger timeouts
#     with fgc_monitor.MonitorPort(foo, 12345, timeout=0.02):
#         futures.wait({fut}, timeout=0.2)

#     assert fut.done()
#     data_dict, data_list, gateway, curr_time = fut.result()
#     assert data_dict is None
#     assert data_list is None
#     assert gateway is None
#     assert isinstance(curr_time, float)

# #def test_monitor_port_timeout_period(monkeypatch, get_rbac_token):
# #
# #    fut = futures.Future()
# #    calls = []
# #
# #    def foo(data_dict, data_list, gateway, curr_time):
# #        calls.append(curr_time)
# #        if len(calls) >= 5:
# #            fut.set_result(True)
# #
# #    monkeypatch.setattr(fgc_monitor, "RETRY_CONNECTION_MARGIN", 10.0) # Margin big enouth to trigger timeouts
# #    with fgc_monitor.MonitorPort(foo, 12345, timeout=0.02):
# #        futures.wait({fut}, timeout=0.5)
# #
# #    assert fut.done()
# #    for i in range(1, len(calls)):
# #        time_diff = calls[i] - calls[i-1]
# #        assert time_diff == pytest.approx(0.02 + fgc_monitor.FGC_CYCLE_TIME, abs=0.005)

# def test_monitor_port_filter_id(get_rbac_token):

#     def foo(*args, **kwargs):
#         fut.set_result(True)

#     with new_udp_stream(GATEWAY_A, 5, 12345, 0xABAB, token=get_rbac_token()):

#         fut = futures.Future()
#         with fgc_monitor.MonitorPort(foo, 12345, filter_id=0xABAB):
#             futures.wait({fut}, timeout=0.2)
#             assert fut.done()

#         fut = futures.Future()
#         with fgc_monitor.MonitorPort(foo, 12345, filter_id={0xABAB, 0x0001}):
#             futures.wait({fut}, timeout=0.2)
#             assert fut.done()

#         fut = futures.Future()
#         with fgc_monitor.MonitorPort(foo, 12345):
#             futures.wait({fut}, timeout=0.2)
#             assert fut.done()

#         fut = futures.Future()
#         with fgc_monitor.MonitorPort(foo, 12345, filter_id=0x0001):
#             futures.wait({fut}, timeout=0.2)
#             assert not fut.done()

# def test_monitor_port_filter_address(get_rbac_token):

#     def foo(*args, **kwargs):
#         fut.set_result(True)

#     with new_udp_stream(GATEWAY_A, 5, 12345, 0, token=get_rbac_token()):

#         fut = futures.Future()
#         with fgc_monitor.MonitorPort(foo, 12345, filter_address=GATEWAY_A):
#             futures.wait({fut}, timeout=0.2)
#             assert fut.done()

#         fut = futures.Future()
#         with fgc_monitor.MonitorPort(foo, 12345, filter_address={GATEWAY_A, GATEWAY_B}):
#             futures.wait({fut}, timeout=0.2)
#             assert fut.done()

#         fut = futures.Future()
#         with fgc_monitor.MonitorPort(foo, 12345):
#             futures.wait({fut}, timeout=0.2)
#             assert fut.done()

#         fut = futures.Future()
#         with fgc_monitor.MonitorPort(foo, 12345, filter_address=GATEWAY_B):
#             futures.wait({fut}, timeout=0.2)
#             assert not fut.done()

# def test_validate_callback_ok():
#     def cb(data_dict, data_list, gateway, timestamp):
#         pass
#     fgc_monitor.validate_callback(cb)

# def test_validate_callback_ok_args():
#     def cb(*args):
#         pass
#     fgc_monitor.validate_callback(cb)

# def test_validate_callback_fail_1():
#     def cb(data_dict, data_list, gateway, timestamp, will_fail):
#         pass
#     with pytest.raises(TypeError):
#         fgc_monitor.validate_callback(cb)

# def test_validate_callback_fail_2():
#     def cb():
#         pass
#     with pytest.raises(TypeError):
#         fgc_monitor.validate_callback(cb)

# def test_validate_callback_err_ok():
#     def cb(err, gateway, timestamp):
#         pass
#     fgc_monitor.validate_callback_err(cb)

# def test_validate_callback_err_ok_args():
#     def cb(*args):
#         pass
#     fgc_monitor.validate_callback_err(cb)

# def test_validate_callback_err_fail_1():
#     def cb(err, gateway, timestamp, will_fail):
#         pass
#     with pytest.raises(TypeError):
#         fgc_monitor.validate_callback_err(cb)

# def test_validate_callback_err_fail_2():
#     def cb():
#         pass
#     with pytest.raises(TypeError):
#         fgc_monitor.validate_callback_err(cb)

# ## EOF
