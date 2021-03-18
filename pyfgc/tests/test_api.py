import asyncio
import pytest
import pyfgc

TARGET_1 = "RFNA.866.06.ETH1"

def test_sync_pyfgc_context_manager_returns_session_default_protocol():
    pass
#     with pyfgc.fgc(TARGET_1) as device:
#         assert isinstance(device, pyfgc.FgcSession)

# @pytest.mark.asyncio
# async def test_async_pyfgc_context_manager_returns_session_default_protocol():
#     async with pyfgc.async_fgc(TARGET_1) as device:
#         assert isinstance(device, pyfgc.FgcAsyncSession)

# def test_sync_pyfgc_context_manager_returns_session_specific_protocol():
#     with pyfgc.fgc(TARGET_1, protocol="sync") as device:
#         assert isinstance(device, pyfgc.FgcSession)

# # TODO: [Test] Target(s) passed in the format str(DEVICE)
# # TODO: [Test] Target names should be case insensitive!
# # TODO: [Test] Even with a name file, connecting with str(DEVICE) to a unknown device should raise an error (?)

# def test_sync_pyfgc_connect_returns_session_default_protocol():
#     device = pyfgc.connect(TARGET_1)
#     assert isinstance(device, pyfgc.FgcSession)

# @pytest.mark.asyncio
# async def test_async_pyfgc_connect_returns_session_default_protocol():
#     device = await pyfgc.async_connect(TARGET_1)
#     assert isinstance(device, pyfgc.FgcAsyncSession)

# def test_sync_pyfgc_connect_returns_session_specific_protocol():
#     device = pyfgc.connect(TARGET_1, protocol="sync")
#     assert isinstance(device, pyfgc.FgcSession)

# def test_sync_pyfgc_connect_throws_correct_exception_type():
#     with pytest.raises(pyfgc.PyFgcError):
#         _ = pyfgc.connect(TARGET_1, protocol="serial")

# def test_sync_pyfgc_get_returns_response_default_protocol():
#     fgc_res = pyfgc.get(TARGET_1, "non_existing_prop")
#     assert isinstance(fgc_res, pyfgc.FgcResponse)

# @pytest.mark.asyncio
# async def test_async_pyfgc_get_returns_response_default_protocol():
#     fgc_res = await pyfgc.async_get(TARGET_1, "non_existing_prop")
#     assert isinstance(fgc_res, pyfgc.FgcSingleResponse)

# def test_sync_pyfgc_get_returns_response_specific_protocol():
#     fgc_res = pyfgc.get(TARGET_1, "property", protocol="sync")
#     assert isinstance(fgc_res, pyfgc.FgcResponse)

# def test_sync_pyfgc_set_returns_response():
#     fgc_res = pyfgc.set(TARGET_1, "property", "value")
#     assert isinstance(fgc_res, pyfgc.FgcResponse)

# @pytest.mark.asyncio
# async def test_async_pyfgc_set_returns_response():
#     fgc_res = await pyfgc.async_set(TARGET_1, "property", "value")
#     assert isinstance(fgc_res, pyfgc.FgcSingleResponse)

# def test_pyfgc_monitor_returns_monitor_session_object():
#     def my_callback(*args, **kwargs):
#         pass
#     fgc_mon = pyfgc.monitor_session(my_callback, TARGET_1, 50)
#     assert isinstance(fgc_mon, pyfgc.MonitorSession)

# def test_pyfgc_monitor_returns_monitor_port_nobject():
#     def my_callback(*args, **kwargs):
#         pass
#     fgc_mon = pyfgc.monitor_port(my_callback, 12345)
#     assert isinstance(fgc_mon, pyfgc.MonitorPort)

# def test_pyfgc_terminal_returns_terminal_object():
#     def my_callback():
#         pass

#     remote_term = pyfgc.terminal(TARGET_1, my_callback)
#     assert isinstance(remote_term, pyfgc.RemoteTerminal)
