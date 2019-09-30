import pytest
import pyfgc

SINGLE_TARGET = "RFNA.866.06.ETH1"

def test_pyfgc_context_manager_returns_session_default_protocol():
    with pyfgc.fgcs(SINGLE_TARGET) as devices:
        assert isinstance(devices, pyfgc.FgcSession)

def test_pyfgc_context_manager_returns_session_specific_protocol():
    with pyfgc.fgcs(SINGLE_TARGET, protocol="async") as devices:
        assert isinstance(devices, pyfgc.FgcSession)

def test_pyfgc_connect_returns_session_default_protocol():
    devices = pyfgc.connect(SINGLE_TARGET)
    assert isinstance(devices, pyfgc.FgcSession)

def test_pyfgc_connect_returns_session_specific_protocol():
    devices = pyfgc.connect(SINGLE_TARGET, protocol="sync")
    assert isinstance(devices, pyfgc.FgcSession)

def test_pyfgc_connect_throws_correct_exception_type():
    with pytest.raises(pyfgc.PyFgcError):
        _ = pyfgc.connect(SINGLE_TARGET, protocol="serial")

def test_pyfgc_disconnect_calls_session_disconnect():
    devices = pyfgc.connect(SINGLE_TARGET)
    assert len(devices) == 1

    pyfgc.disconnect(devices)
    assert len(devices) == 0

def test_pyfgc_get_returns_response_default_protocol():
    fgc_res = pyfgc.get(SINGLE_TARGET, "non_existing_prop")
    assert isinstance(fgc_res, pyfgc.FgcResponse)

def test_pyfgc_get_returns_response_specific_protocol():
    fgc_res = pyfgc.get(SINGLE_TARGET, "property", protocol="sync")
    assert isinstance(fgc_res, pyfgc.FgcResponse)

def test_pyfgc_set_returns_response():
    fgc_res = pyfgc.set(SINGLE_TARGET, "property", "value")
    assert isinstance(fgc_res, pyfgc.FgcResponse)

def test_pyfgc_monitor_returns_monitor_object():
    def my_callback():
        pass

    fgc_mon = pyfgc.monitor(SINGLE_TARGET, my_callback)
    assert isinstance(fgc_mon, pyfgc.Monitor)

def test_pyfgc_terminal_returns_terminal_object():
    def my_callback():
        pass

    remote_term = pyfgc.terminal(SINGLE_TARGET, my_callback)
    assert isinstance(remote_term, pyfgc.RemoteTerminal)
