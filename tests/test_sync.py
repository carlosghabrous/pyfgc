import struct
from functools import reduce

import pytest
import pyfgc_name
import pyfgc


device_1 = "RFNA.866.06.ETH1"
device_2 = "RFNA.866.01.ETH2"
device_3 = "RFNA.866.02.ETH3"
devs_list = [device_1, device_3, "RFNA.866.01.ETH3"]
devs_regex = "^RFNA\.866\.d{1,}\.ETH\d$"

pyfgc_name.read_name_file()


def test_sync_connect_disconnect_single():
    """
    Connects to a single device using the context manager.
    """

    gw = pyfgc_name.devices[device_1]["gateway"]

    with pyfgc.fgcs(device_1) as fgcs:
        assert 1 == len(fgcs)
        assert None != pyfgc.protocols.sync_fgc.available_connections[gw]["socket"]

    assert 0 == len(pyfgc.protocols.sync_fgc.available_connections)


def test_sync_connect_disconnect_list():
    """
    Connects to multiple (list) using the context manager.
    """
    gws = {pyfgc_name.devices[d]["gateway"] for d in devs_list} 

    with pyfgc.fgcs(devs_list, protocol="sync") as fgcs:
        assert len(devs_list) == len(fgcs)
        for gw in gws:
            assert None != pyfgc.protocols.sync_fgc.available_connections[gw]["socket"]

    assert 0 == len(pyfgc.protocols.sync_fgc.available_connections)


def test_sync_connect_after():
    """
    Connects to multiple using the `connect` function.
    
    This test is just to demonstrate that connecting to multiple devices
    can happen in several steps (not once at the beginning). Also, the user 
    can specify which to disconnect from.
    """

    gws = {pyfgc_name.devices[d]["gateway"] for d in devs_list}
    
    try:
        fgcs = pyfgc.connect(devs_list)
        assert len(devs_list) == len(fgcs)
        for gw in gws:
            assert None != pyfgc.protocols.sync_fgc.available_connections[gw]["socket"]

        fgcs.add_connection(device_2)
        assert len(devs_list) + 1 == len(fgcs)

        gws.add(pyfgc_name.devices[device_2]["gateway"])
        for gw in gws:
            assert None != pyfgc.protocols.sync_fgc.available_connections[gw]["socket"]

        fgcs.disconnect(devs_list)
        assert 1 == len(fgcs)

        fgcs.disconnect(device_2)
        assert 0 == len(fgcs)

        fgcs = pyfgc.connect(devs_list)

    except Exception:
        raise

    finally:
        if fgcs:
            fgcs.disconnect()


    assert 0 == len(fgcs)
    assert 0 == len(pyfgc.protocols.sync_fgc.available_connections)


def test_sync_targets_and_available():
    """
    Connects to multiple  examining target and available targets.
    
    The ` argument for the `connect` function are considered targets.
    On the background, the library will also keep track of the available targets
    of each gateway (all the FGCs that exist on a gateways' network)
    """

    gws = {pyfgc_name.devices[d]["gateway"] for d in devs_list}
    lengths = [len(pyfgc_name.gateways[gw]["devices"]) for gw in gws]
    available = reduce((lambda x, y : x + y), lengths)

    with pyfgc.fgcs(devs_list, "sync") as fgcs:
        assert len(devs_list) == len(fgcs)
        avail_connections = pyfgc.protocols.sync_fgc.available_connections

        avail_fgcs = 0
        for gw in avail_connections:
            avail_fgcs += len(avail_connections[gw]["devices"])

        assert available ==  avail_fgcs


def test_sync_get_with_empty_list_raises_exception():
    """
    Makes sure passing nothing as argument is handled gracefully.

    Makes use of the three flavors the library has to perform get/set operations.
    
    """
    
    my_devs = []
    prop = "DEVICE.NAME"

    with pytest.raises(pyfgc.PyFgcError):
        _ = pyfgc.get(my_devs, prop)

    with pytest.raises(pyfgc.PyFgcError):
        with pyfgc.fgcs(my_devs):
            _ = pyfgc.get(prop)

    try:
        fgcs = pyfgc.connect(my_devs)
        r = fgcs.get(prop)
        assert len(r) == len(my_devs)

    except pyfgc.PyFgcError:
        fgcs = None

    finally:
        if fgcs:
            fgcs.disconnect()


def test_sync_get_single():
    """
    Gets property from device.

    """

    prop = "DEVICE.NAME"

    r = pyfgc.get(device_1, prop)
    try:
        assert r.value == device_1

    except pyfgc.FgcResponseError:
        # Just in case the device was not operational
        print(f"Error, device {device_1}, err_code {r.err_code}, err_msg {r.err_msg}")


def test_sync_get_single_option():
    """
    Gets a property from a single device, specifying an option.
    
    """

    prop = "LIMITS.I.EARTH"

    r = pyfgc.get(device_1, prop, get_option="HEX")
    try:
        int(r.value, 16)

    except ValueError:
        print(f"Property {prop} from device {device_1} is not a valid hex value: {r.value}!")
        assert False

    except pyfgc.FgcResponseError:
        print(f"Error, device {device_1}, err_code {r.err_code}, err_msg {r.err_msg}")


def test_sync_get_single_binary():
    """
    Gets a property in binary format.
    """
    r = pyfgc.get(device_1, "LOG.PM.SPY.IEARTH", get_option="bin")
    try:
        length_header_decoded = struct.unpack("!L", r.value[0:4])[0]
        actual_length = len(r.value[4:])
        assert len(length_header_decoded) == actual_length
    
    except pyfgc.FgcResponseError:
        print(f"Error, device {device_1}, err_code {r.err_code}, err_msg {r.err_msg}")


def test_sync_get_single_parent():
    """
    Gets a parent property from a single device.
    """

    prop = "BARCODE"
    r = pyfgc.get(device_1, prop)
    try:
        assert isinstance(r.value, str)

    except pyfgc.FgcResponseError:
        print(f"Error, device {device_1}, err_code {r.err_code}, err_msg {r.err_msg}")


def test_sync_get_multiple():
    """
    Gets property from multiple  passed as a list.
    
    """

    prop = "DEVICE.NAME"

    r = pyfgc.get(devs_list, prop)
    assert len(r), len(devs_list)

    for dev in r:
        assert (dev in devs_list)

        try:
            assert r[dev].value == dev
        except pyfgc.FgcResponseError:
            print(f"Error, device {dev}, err_code {r[dev].err_code}, err_msg {r[dev].err_msg}")


def test_sync_get_multiple_subset():
    """
    Gets from a subset of connected 

    We connect to a set of and a command is sent to them. 
    Later a command is sent to a subset of them.
    
    """

    prop = "DEVICE.NAME"

    with pyfgc.fgcs(devs_list) as fgcs:
        r = fgcs.get(prop)
        assert len(r) == len(devs_list)

        for dev in r:
            assert (dev in devs_list)
            try:
                assert r[dev].value == dev
            except pyfgc.FgcResponseError:
                print(f"Error, device {dev}, err_code {r[dev].err_code}, err_msg {r[dev].err_msg}")

        r = fgcs.get(prop, targets=device_1)
        assert device_1 == r.value
        try:
            assert device_1 == r.value
        except pyfgc.FgcResponseError:
            print(f"Error, device {device_1}, err_code {r.err_code}, err_msg {r.err_msg}")


def test_sync_set_single():
    """
    Sends a set command to a single device.
    
    Runs a get command to verify that the set command took place.        
    """
    
    prop = "LIMITS.I.EARTH"
    value = 1e-2

    with pyfgc.fgcs(device_1) as fgcs:
        r = fgcs.set(prop, value)

        r = fgcs.get(prop)

        try:
            assert float(r.value) == value
        except pyfgc.FgcResponseError:
            print(f"Error, device {device_1}, err_code {r.err_code}, err_msg {r.err_msg}")


def test_sync_set_multiple():
    """
    Set command on multiple 
    
    [description]
    """

    prop = "LIMITS.I.EARTH"
    value = 5.5

    with pyfgc.fgcs(devs_list, protocol="sync") as fgcs:
        r = fgcs.set(prop, value)

        r = fgcs.get(prop)
        for dev in r:
            assert (dev in devs_list)
            try:
                assert float(r[dev].value) == value
            except pyfgc.FgcResponseError:
                print(f"Error, device {dev}, err_code {r[dev].err_code}, err_msg {r[dev].err_msg}")

def test_reuse_connection():
    prop = "DEVICE.NAME"

    def get_connection_and_get(fgc):
        r = fgc.get(prop)
        return r

    with pyfgc.fgcs(device_1) as fgcs:
        response = get_connection_and_get(fgcs)
        assert response.value == device_1