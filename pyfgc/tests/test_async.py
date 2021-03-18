# import os
# import time
# import struct
# import asyncio
# import struct
# import concurrent.futures

# import pytest
# import pyfgc_name
# import pyfgc_rbac
# import pyfgc

# from pyfgc.protocols.async_fgc import AsyncFgcProtocol
# from pyfgc.fgc_response import FgcSingleResponse, FgcResponseError

# gateway_1 = "CFC-866-RETH1"
# gateway_2 = "CFC-866-RETH2"
# device_1 = "RFNA.866.06.ETH1"
# device_2 = "RFNA.866.01.ETH2"
# port = 1905

# pyfgc_name.read_name_file()

# # Test protocol object

# def truncate_float(value, precision):
#     string_def = "{{:.{}f}}".format(precision)
#     return float(string_def.format(value))

# @pytest.fixture
# def send_rbac():
#     async def _send_rbac(protocol):
#         token = pyfgc_rbac.get_token_location()
#         response_fut = asyncio.ensure_future(protocol.set("CLIENT.TOKEN", token))
#         response = await asyncio.wait_for(response_fut, 1.0)
#         response.value
#     return _send_rbac

# @pytest.mark.asyncio
# async def test_protocol_connection(event_loop):
#     _, protocol = await event_loop.create_connection(lambda: AsyncFgcProtocol(event_loop), gateway_1, port)
#     assert isinstance(protocol, AsyncFgcProtocol)

# @pytest.mark.asyncio
# async def test_protocol_set(event_loop):
#     _, protocol = await event_loop.create_connection(lambda: AsyncFgcProtocol(event_loop), gateway_1, port)
#     response_fut = asyncio.ensure_future(protocol.set("TEST.FLOAT", 123.456, device=device_1))
#     response = await asyncio.wait_for(response_fut, 1.0)
#     assert isinstance(response, FgcSingleResponse)

# @pytest.mark.asyncio
# async def test_protocol_get(event_loop):
#     _, protocol = await event_loop.create_connection(lambda: AsyncFgcProtocol(event_loop), gateway_1, port)
#     response_fut = asyncio.ensure_future(protocol.get("TEST.FLOAT", device=device_1))
#     response = await asyncio.wait_for(response_fut, 1.0)
#     assert isinstance(response, FgcSingleResponse)

# @pytest.mark.asyncio
# async def test_protocol_set_value(event_loop, send_rbac):
#     _, protocol = await event_loop.create_connection(lambda: AsyncFgcProtocol(event_loop), gateway_1, port)
#     await send_rbac(protocol)
#     response_fut = asyncio.ensure_future(protocol.set("TEST.FLOAT", 111, device=device_1))
#     response = await asyncio.wait_for(response_fut, 1.0)
#     response.value

# @pytest.mark.asyncio
# async def test_protocol_set_value_error(event_loop, send_rbac):
#     _, protocol = await event_loop.create_connection(lambda: AsyncFgcProtocol(event_loop), gateway_1, port)
#     await send_rbac(protocol)
#     response_fut = asyncio.ensure_future(protocol.set("TEST.FLOAT", "will fail", device=device_1))
#     response = await asyncio.wait_for(response_fut, 1.0)
#     with pytest.raises(FgcResponseError, match=r'bad float'): # No rbac token was set
#         response.value

# @pytest.mark.asyncio
# async def test_protocol_set_get_value(event_loop, send_rbac):
#     float_value = 777.777
#     _, protocol = await event_loop.create_connection(lambda: AsyncFgcProtocol(event_loop), gateway_1, port)
#     await send_rbac(protocol)
#     # Set value
#     response_fut = asyncio.ensure_future(protocol.set("TEST.FLOAT", float_value, device=device_1))
#     response = await asyncio.wait_for(response_fut, 1.0)
#     # Get value and confirm result
#     response_fut = asyncio.ensure_future(protocol.get("TEST.FLOAT", device=device_1))
#     response = await asyncio.wait_for(response_fut, 1.0)
#     assert pytest.approx(float(response.value)) == float_value

# property_list = [
#     ("TEST.FLOAT",  0, 777.777),   # bytes [0:3]   - pos 0/4 = 0
#     ("TEST.INT8S",  4, -16),       # bytes [4]     - pos 4/1 = 4
#     ("TEST.INT8U",  5, 61),        # bytes [5]     - pos 5/1 = 5
#     ("TEST.INT16S", 3, -1221),     # bytes [6:7]   - pos 6/2 = 3
#     ("TEST.INT16U", 4, 2112),      # bytes [8:9]   - pos 8/2 = 4
#     ("TEST.INT32S", 3, -123454321),# bytes [12:15] - pos 12/4 = 3
#     ("TEST.INT32U", 4, 543212345), # bytes [16:19] - pos 16/4 = 4
# ]

# @pytest.mark.asyncio
# async def test_protocol_multiple_set_value(event_loop, send_rbac):
#     _, protocol = await event_loop.create_connection(lambda: AsyncFgcProtocol(event_loop), gateway_1, port)
#     await send_rbac(protocol)

#     futures = set()
#     for prop, idx, val in property_list:
#         new_future = asyncio.ensure_future(protocol.set(prop+f"[{idx}]", val, device=device_1))
#         futures.add(new_future)

#     done, not_done = await asyncio.wait(futures, timeout=1.0)

#     assert not not_done
#     for fut_done in done:
#         fut_done.result().value

# @pytest.mark.asyncio
# async def test_protocol_multiple_set_get_value(event_loop, send_rbac):
#     _, protocol = await event_loop.create_connection(lambda: AsyncFgcProtocol(event_loop), gateway_1, port)
#     await send_rbac(protocol)

#     # Set values
#     futures = set()
#     for prop, idx, val in property_list:
#         new_future = asyncio.ensure_future(protocol.set(prop+f"[{idx}]", val, device=device_1))
#         futures.add(new_future)

#     done, not_done = await asyncio.wait(futures, timeout=1.0)

#     assert not not_done
#     for fut_done in done:
#         fut_done.result().value

#     # Get values and confirm result
#     futures = dict()
#     for prop, idx, val in property_list:
#         new_future = asyncio.ensure_future(protocol.get(prop+f"[{idx}]", device=device_1))
#         futures[new_future] = val

#     done, not_done = await asyncio.wait(futures.keys(), timeout=1.0)

#     assert not not_done

#     for fut_done in done:
#         assert pytest.approx(futures[fut_done]) == float(fut_done.result().value)

# binary_data_streams = [
#     b"1234567890",
#     b"abcdefghij",
#     b"0000000000",
#     b"a1b2c3d4e5",
#     b"abcdef\n;",
#     b"$$$$$$$$",
#     b";;;;;;;;",
#     b"\n\n\n\n",
#     b"\n;\n;\n;\n;",
#     b"$ .\n\n;",
#     b"$ !\n\n;",
#     b"$ .\n\n;$ .\n\n;$ .\n\n;$ .\n\n;",
#     b"\x00\x00\x00\x00",
#     b"\xff\xff\xff\xff",
#     os.urandom(1),
#     os.urandom(64),
# ]

# @pytest.mark.parametrize("input_data", binary_data_streams)
# @pytest.mark.asyncio
# async def test_protocol_set_get_binary(event_loop, send_rbac, input_data):
#     str_value = input_data
#     _, protocol = await event_loop.create_connection(lambda: AsyncFgcProtocol(event_loop), gateway_1, port)
#     await send_rbac(protocol)
#     # Set value
#     response_fut = asyncio.ensure_future(protocol.set("TEST.BIN", str_value))
#     response = await asyncio.wait_for(response_fut, 1.0)
#     # Get value and confirm result
#     response_fut = asyncio.ensure_future(protocol.get("TEST.BIN BIN"))
#     response = await asyncio.wait_for(response_fut, 1.0)
#     bin_value = response.value
#     length = struct.unpack('>I', bin_value[:4])[0]
#     assert length == len(str_value)
#     assert length + 4 == len(bin_value)

# log_properties = [
#     "LOG.EVT",
#     "LOG.SPY.DATA[0]",
#     "LOG.SPY.DATA[1]",
#     "LOG.SPY.DATA[2]",
#     "LOG.SPY.DATA[3]",
# ]

# @pytest.mark.parametrize("input_prop", log_properties)
# @pytest.mark.asyncio
# async def test_protocol_get_long_binary(event_loop, send_rbac, input_prop):
#     _, protocol = await event_loop.create_connection(lambda: AsyncFgcProtocol(event_loop), gateway_1, port)
#     await send_rbac(protocol)

#     # BIN DATA|{time_origin_s},{time_offset_ms},{time_duration_ms},0
#     get_opt = f"BIN DATA|{time.time():.6f},2000,2000,0"

#     response_fut = asyncio.ensure_future(protocol.get(input_prop, get_option=get_opt, device=device_1))
#     response = await asyncio.wait_for(response_fut, 2.0)
#     bin_value = response.value
#     length = struct.unpack('>I', bin_value[:4])[0]
#     assert length + 4 == len(bin_value)

# @pytest.mark.asyncio
# async def test_protocol_stream(event_loop, send_rbac):
#     _, protocol = await event_loop.create_connection(lambda: AsyncFgcProtocol(event_loop), gateway_1, port)
#     stream_reader = protocol.get_stream_reader()
#     await send_rbac(protocol)

#     # Check before opening raw connection - streamreader should stay empty
#     await asyncio.sleep(0.1)
#     with pytest.raises(asyncio.TimeoutError):
#         await asyncio.wait_for(stream_reader.read(4), 0.5)

#     # Check after opening raw connection - streamreader should contain bytes
#     await protocol.enable_rterm_mode(4)
#     raw_data = await asyncio.wait_for(stream_reader.read(4), 0.5)
#     assert len(raw_data)

# # Test top level API

# @pytest.mark.asyncio
# async def test_async_get_single():
#     """Gets property from device."""

#     prop = "DEVICE.NAME"
#     r = await pyfgc.async_get(device_1, prop)

#     try:
#         assert r.value == device_1
#     except pyfgc.FgcResponseError:
#         # Just in case the device was not operational
#         print(f"Error, device {device_1}, err_code {r.err_code}, err_msg {r.err_msg}")

# @pytest.mark.asyncio
# async def test_async_get_single_option():
#     """Gets a property from a single device, specifying an option."""

#     prop = "LIMITS.I.EARTH"
#     r = await pyfgc.async_get(device_1, prop, get_option="HEX")

#     try:
#         int(r.value, 16)
#     except ValueError:
#         print(f"Property {prop} from device {device_1} is not a valid hex value: {r.value}!")
#         raise
#     except pyfgc.FgcResponseError:
#         print(f"Error, device {device_1}, err_code {r.err_code}, err_msg {r.err_msg}")
#         raise

# @pytest.mark.asyncio
# async def test_async_get_single_binary():
#     """Gets a property in binary format."""

#     r = await pyfgc.async_set(gateway_1, "TEST.BIN", b"binary_data")
#     r.value
#     r = await pyfgc.async_get(gateway_1, "TEST.BIN", get_option="bin")
#     try:
#         length_header_decoded = struct.unpack("!L", r.value[0:4])[0]
#         actual_length = len(r.value[4:])
#         assert length_header_decoded == actual_length
#     except pyfgc.FgcResponseError:
#         print(f"Error, device {device_1}, err_code {r.err_code}, err_msg {r.err_msg}")
#         raise

# @pytest.mark.asyncio
# async def test_async_get_single_parent():
#     """Gets a parent property from a single device."""

#     prop = "BARCODE"
#     r = await pyfgc.async_get(device_1, prop)
#     try:
#         assert isinstance(r.value, str)
#     except pyfgc.FgcResponseError:
#         print(f"Error, device {device_1}, err_code {r.err_code}, err_msg {r.err_msg}")
#         raise

# @pytest.mark.asyncio
# async def test_async_set_single():
#     """Sends a set command to a single device.
#     Runs a get command to verify that the set command took place.
#     """

#     prop = "LIMITS.I.EARTH"
#     value = 1e-2

#     async with pyfgc.async_fgc(device_1) as fgc:
#         r = await fgc.set(prop, value)
#         r = await fgc.get(prop)

#         try:
#             assert pytest.approx(float(r.value)) == value
#         except pyfgc.FgcResponseError:
#             print(f"Error, device {device_1}, err_code {r.err_code}, err_msg {r.err_msg}")
#             raise

# @pytest.mark.asyncio
# async def test_multiple_devices():
#     """Tests sending a command to multiple FGCs in parallel"""

#     #device_names = pyfgc_name.build_device_set(".*866.*ETH1")
#     device_names = pyfgc_name.build_device_set(".*866.*ETH1")

#     fut_results = dict()
#     for dev in device_names:
#         fut_results[dev] = asyncio.ensure_future(pyfgc.async_get(dev, "DEVICE.NAME"))

#     await asyncio.wait(fut_results.values(), timeout=1.0)

#     for k, v in fut_results.items():
#         rsp = v.result()
#         try:
#             assert k == rsp.value
#         except FgcResponseError:
#             # This is also a valid response for this test
#             with pytest.raises(FgcResponseError, match=r'dev not ready'):
#                 rsp.value

# @pytest.mark.asyncio
# async def test_multiple_devices_plus():
#     """Tests sending a command to multiple FGCs in parallel (more commands!)"""

#     device_names = pyfgc_name.build_device_set(".*866.*ETH1")

#     # Set multiple values for many devices
#     fut_results = list()
#     for dev in device_names:
#         for prop, idx, val in property_list:
#             fut = asyncio.ensure_future(pyfgc.async_set(dev, prop+f"[{idx}]", val))
#             fut_results.append(fut)

#     done, not_done = await asyncio.wait(fut_results, timeout=5.0)
#     assert not not_done

#     # Get multiple values from many devices
#     fut_results = list()
#     for dev in device_names:
#         for prop, idx, val in property_list:
#             fut = asyncio.ensure_future(pyfgc.async_get(dev, prop+f"[{idx}]"))
#             fut_results.append((fut, val))

#     done, not_done = await asyncio.wait({fut for fut,_ in fut_results}, timeout=5.0)
#     assert not not_done

#     for fut, val in fut_results:
#         rsp = fut.result()
#         try:
#             assert pytest.approx(val) == float(rsp.value)
#         except FgcResponseError:
#             # This is also a valid response for this test
#             with pytest.raises(FgcResponseError, match=r'dev not ready'):
#                 rsp.value

# @pytest.mark.asyncio
# async def test_socket_failure_before_coroutine():
#     async with pyfgc.async_fgc(device_1) as fgc:
#         fgc._protocol_object.protocol.transport.close()
#         with pytest.raises(RuntimeError):
#             await fgc.get("TEST.FLOAT")

# @pytest.mark.asyncio
# async def test_socket_failure_middle_coroutine(monkeypatch):

#     async with pyfgc.async_fgc(device_1) as fgc:
#         prev_send = fgc._protocol_object.protocol.send
#         async def send_and_close(data):
#             await prev_send(data)
#             fgc._protocol_object.protocol.transport.close()

#         monkeypatch.setattr(fgc._protocol_object.protocol, "send", send_and_close)
#         fut_coroutine = asyncio.ensure_future(fgc.get("TEST.FLOAT"))

#         with pytest.raises(asyncio.CancelledError):
#             await asyncio.wait_for(fut_coroutine, 5.0)



# # EOF
